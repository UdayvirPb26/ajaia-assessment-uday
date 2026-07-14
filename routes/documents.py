from flask import Blueprint, request, jsonify, render_template, abort, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Document, SharedAccess, User
from extensions import db
from file_import import file_to_delta, UnsupportedFileType, MAX_UPLOAD_BYTES

docs_bp = Blueprint("documents", __name__)


@docs_bp.route("/documents", methods=["GET"])
@login_required
def list_documents():
    owned = Document.query.filter_by(owner_id=current_user.id).order_by(Document.updated_at.desc()).all()

    shared = (
        Document.query
        .join(SharedAccess, SharedAccess.document_id == Document.id)
        .filter(SharedAccess.user_id == current_user.id)
        .order_by(Document.updated_at.desc())
        .all()
    )

    return render_template("documents_list.html", documents=owned, shared_documents=shared)


@docs_bp.route("/documents", methods=["POST"])
@login_required
def create_document():
    doc = Document(title="Untitled Document", content="{}", owner_id=current_user.id)
    db.session.add(doc)
    db.session.commit()
    return redirect(url_for("documents.edit_document", doc_id=doc.id))

@docs_bp.route("/documents/upload", methods=["POST"])
@login_required
def upload_document():
    if "file" not in request.files:
        flash("No file selected.")
        return redirect(url_for("documents.list_documents"))

    uploaded = request.files["file"]
    if uploaded.filename == "":
        flash("No file selected.")
        return redirect(url_for("documents.list_documents"))

    file_bytes = uploaded.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        flash("File too large. Max size is 2MB.")
        return redirect(url_for("documents.list_documents"))

    try:
        title, delta_json = file_to_delta(uploaded.filename, file_bytes)
    except UnsupportedFileType as e:
        flash(str(e))
        return redirect(url_for("documents.list_documents"))
    except Exception:
        flash("Could not read this file. It may be corrupted or in an unexpected format.")
        return redirect(url_for("documents.list_documents"))

    doc = Document(title=title, content=delta_json, owner_id=current_user.id)
    db.session.add(doc)
    db.session.commit()
    flash(f'Imported "{title}" successfully.')
    return redirect(url_for("documents.edit_document", doc_id=doc.id))

@docs_bp.route("/documents/<int:doc_id>", methods=["GET"])
@login_required
def edit_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not _can_access(doc, current_user):
        abort(403)

    is_owner = doc.owner_id == current_user.id
    shares = []
    if is_owner:
        shares = (
            db.session.query(SharedAccess, User)
            .join(User, User.id == SharedAccess.user_id)
            .filter(SharedAccess.document_id == doc.id)
            .all()
        )

    return render_template("editor.html", document=doc, is_owner=is_owner, shares=shares)


@docs_bp.route("/api/documents/<int:doc_id>", methods=["PATCH"])
@login_required
def update_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not _can_edit(doc, current_user):
        abort(403)

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = (data.get("title") or "").strip()
        doc.title = title or "Untitled Document"

    if "content" in data:
        doc.content = data.get("content") or "{}"

    db.session.commit()
    return jsonify(doc.to_dict())


@docs_bp.route("/documents/<int:doc_id>/share", methods=["POST"])
@login_required
def share_document(doc_id):
    doc = Document.query.get_or_404(doc_id)

    if doc.owner_id != current_user.id:
        abort(403)

    username = (request.form.get("username") or "").strip()
    if not username:
        flash("Enter a username to share with.")
        return redirect(url_for("documents.edit_document", doc_id=doc.id))

    target_user = User.query.filter_by(username=username).first()
    if not target_user:
        flash(f'No user found with username "{username}".')
        return redirect(url_for("documents.edit_document", doc_id=doc.id))

    if target_user.id == current_user.id:
        flash("You already own this document.")
        return redirect(url_for("documents.edit_document", doc_id=doc.id))

    existing = SharedAccess.query.filter_by(document_id=doc.id, user_id=target_user.id).first()
    if existing:
        flash(f'Already shared with "{username}".')
        return redirect(url_for("documents.edit_document", doc_id=doc.id))

    grant = SharedAccess(document_id=doc.id, user_id=target_user.id)
    db.session.add(grant)
    db.session.commit()
    flash(f'Shared with "{username}".')
    return redirect(url_for("documents.edit_document", doc_id=doc.id))


@docs_bp.route("/documents/<int:doc_id>/share/<int:user_id>/revoke", methods=["POST"])
@login_required
def revoke_share(doc_id, user_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.owner_id != current_user.id:
        abort(403)

    grant = SharedAccess.query.filter_by(document_id=doc.id, user_id=user_id).first()
    if grant:
        db.session.delete(grant)
        db.session.commit()
        flash("Access revoked.")
    return redirect(url_for("documents.edit_document", doc_id=doc.id))


def _can_access(doc, user):
    if doc.owner_id == user.id:
        return True
    return SharedAccess.query.filter_by(document_id=doc.id, user_id=user.id).first() is not None


def _can_edit(doc, user):
    # Scope decision: anyone with shared access can edit (no separate
    # view-only role in this version — see README "Role-based permissions"
    # under stretch goals).
    return _can_access(doc, user)
