from app.config import settings
print(f"Type: {type(settings)}")
print(f"APP_ENV: {settings.APP_ENV}")
print(f"Model dump: {settings.model_dump()}")
