from fastapi import APIRouter, Body, Depends, HTTPException

from app.deps import csrf_protect, require_roles
from app.integrations.r2 import ALLOWED_MIME, get_upload_signer, new_key
from app.models import StaffRole
from app.schemas import UploadSignRequest, UploadSignResponse

router = APIRouter(prefix="/v1/admin/uploads", tags=["admin-uploads"])

# Florists upload bouquet photos, so FLORIST is allowed alongside OWNER/MANAGER.
_can = Depends(require_roles(StaffRole.OWNER, StaffRole.MANAGER, StaffRole.FLORIST))
_csrf = Depends(csrf_protect)


@router.post(
    "/sign",
    response_model=UploadSignResponse,
    operation_id="signUpload",
    dependencies=[_can, _csrf],
)
async def sign_upload(
    body: UploadSignRequest = Body(default_factory=UploadSignRequest),
) -> UploadSignResponse:
    if body.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_type",
                "message": f"Allowed: {', '.join(sorted(ALLOWED_MIME))}",
            },
        )
    key = new_key(body.content_type)
    signed = get_upload_signer().sign_put(key, body.content_type)
    return UploadSignResponse(
        upload_url=signed.upload_url, public_url=signed.public_url
    )
