import logging
from typing import Literal
from pydantic import BaseSettings


class ProgramSettings(BaseSettings):
    temp_output_dir: str = "temp"
    final_output_dir: str = "../"
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


settings = ProgramSettings()
# Configure logging
logging.basicConfig(
    level=settings.logging_level, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
