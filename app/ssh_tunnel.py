import os
import logging
from typing import Optional, Tuple
from sshtunnel import SSHTunnelForwarder

logger = logging.getLogger(__name__)


class SSHTunnelManager:
    """Manages SSH tunnel connections for database access."""
    
    def __init__(self):
        self.tunnel: Optional[SSHTunnelForwarder] = None
        self.local_port: Optional[int] = None
    
    def create_tunnel(self) -> Tuple[str, int]:
        """
        Create an SSH tunnel to the PostgreSQL server.
        
        Returns:
            Tuple of (local_host, local_port) for the tunnel endpoint
            
        Raises:
            ValueError: If required environment variables are missing
            RuntimeError: If tunnel creation fails
        """
        # Get SSH configuration from environment variables
        ssh_host = os.getenv("SSH_HOST")
        ssh_user = os.getenv("SSH_USER") 
        ssh_key_path = os.getenv("SSH_KEY_PATH")
        postgres_host = os.getenv("SSH_POSTGRES_HOST", "localhost")
        postgres_port = int(os.getenv("SSH_POSTGRES_PORT", "5432"))
        
        if not all([ssh_host, ssh_user, ssh_key_path]):
            raise ValueError(
                "SSH configuration missing. Required: SSH_HOST, SSH_USER, SSH_KEY_PATH"
            )
            
        if not os.path.exists(ssh_key_path):
            raise ValueError(f"SSH key file not found: {ssh_key_path}")
        
        logger.info(f"Creating SSH tunnel to {ssh_host} for PostgreSQL at {postgres_host}:{postgres_port}")
        logger.info(f"SSH key path: {ssh_key_path}, exists: {os.path.exists(ssh_key_path)}")
        
        try:
            # Create SSH tunnel
            self.tunnel = SSHTunnelForwarder(
                ssh_host,
                ssh_username=ssh_user,
                ssh_pkey=ssh_key_path,
                remote_bind_address=(postgres_host, postgres_port)
            )
            
            # Start the tunnel
            self.tunnel.start()
            
            if not self.tunnel.is_active:
                raise RuntimeError("Failed to establish SSH tunnel")
                
            self.local_port = self.tunnel.local_bind_port
            local_host = 'localhost'
            
            logger.info(f"SSH tunnel established: {local_host}:{self.local_port} -> {ssh_host} -> {postgres_host}:{postgres_port}")
            
            return local_host, self.local_port
            
        except Exception as e:
            logger.error(f"Failed to create SSH tunnel: {e}")
            if self.tunnel:
                self.tunnel.stop()
                self.tunnel = None
            raise RuntimeError(f"SSH tunnel creation failed: {e}")
    
    def close_tunnel(self):
        """Close the SSH tunnel if it exists."""
        if self.tunnel and self.tunnel.is_active:
            logger.info("Closing SSH tunnel")
            self.tunnel.stop()
            self.tunnel = None
            self.local_port = None
        else:
            logger.debug("No active SSH tunnel to close")
    
    def is_active(self) -> bool:
        """Check if the SSH tunnel is active."""
        return self.tunnel is not None and self.tunnel.is_active
    
    def get_connection_string(self) -> str:
        """
        Build PostgreSQL connection string for the SSH tunnel.
        
        Returns:
            Connection string for SQLAlchemy
            
        Raises:
            RuntimeError: If tunnel is not active
        """
        if not self.is_active():
            raise RuntimeError("SSH tunnel is not active")
            
        postgres_user = os.getenv("SSH_POSTGRES_USER", "postgres")
        postgres_password = os.getenv("SSH_POSTGRES_PASSWORD", "postgres")
        postgres_db = os.getenv("SSH_POSTGRES_DB", "postgres")
        
        return f"postgresql+asyncpg://{postgres_user}:{postgres_password}@localhost:{self.local_port}/{postgres_db}"