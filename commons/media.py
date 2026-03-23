
def upload_media(file_bytes: bytes, filename: str, folder: str = "the-commons") -> dict:
    try:
        import cloudinary
        import cloudinary.uploader
        from .config import config
        cloudinary.config(
            cloud_name = config.cloudinary_cloud_name,
            api_key    = config.cloudinary_api_key,
            api_secret = config.cloudinary_api_secret,
            secure     = True
        )
        result = cloudinary.uploader.upload(
            file_bytes,
            folder          = folder,
            resource_type   = "auto",
            use_filename    = True,
            unique_filename = True,
        )
        return {"ok": True, "url": result["secure_url"], "public_id": result["public_id"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
