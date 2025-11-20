import subprocess
import shlex
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.cli import EchoRequest, EchoResponse
from ..security import get_api_key

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cli", tags=["cli"])


@router.post("/echo", response_model=EchoResponse)
async def echo_message(payload: EchoRequest, api_key: str = Depends(get_api_key)):
    """
    Echo a message to the command line using subprocess.
    
    This endpoint receives a message and executes an echo command
    to output the message to the command line. The message is
    validated for security to prevent shell injection attacks.
    """
    try:
        # Use shlex.quote to safely escape the message for shell execution
        safe_message = shlex.quote(payload.message)
        
        # Execute echo command with the safe message
        # Using shell=True with a properly escaped message is safe here
        result = subprocess.run(
            f"echo {safe_message}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10  # Prevent hanging commands
        )
        
        if result.returncode == 0:
            logger.info(f"Echo command executed successfully: {payload.message}")
            return EchoResponse(
                success=True,
                message=payload.message,
                output=result.stdout.strip()
            )
        else:
            logger.error(f"Echo command failed with return code {result.returncode}: {result.stderr}")
            return EchoResponse(
                success=False,
                message=payload.message,
                error=f"Command failed with return code {result.returncode}: {result.stderr}"
            )
    
    except subprocess.TimeoutExpired:
        logger.error(f"Echo command timed out for message: {payload.message}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Command execution timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error executing echo command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )