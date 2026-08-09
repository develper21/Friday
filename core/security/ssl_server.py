"""
SSL/TLS Server Module
Provides secure HTTP server with SSL/TLS encryption
"""

import ssl
import logging
import ipaddress
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    import datetime
except ImportError:
    raise ImportError("cryptography library is required for SSL server")

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security-related error"""
    pass


class SecureHTTPServer:
    """Provides SSL/TLS enabled HTTP server"""
    
    @staticmethod
    def generate_self_signed_cert(
        common_name: str = "localhost",
        organization: str = "JeanMax",
        validity_days: int = 365
    ) -> Tuple[str, str]:
        """
        Generate self-signed SSL certificate
        
        Args:
            common_name: Common name for certificate
            organization: Organization name
            validity_days: Certificate validity in days
            
        Returns:
            Tuple of (cert_path, key_path)
        """
        config_dir = Path.home() / ".config" / "jean"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        cert_path = config_dir / "cert.pem"
        key_path = config_dir / "key.pem"
        
        # Check if certificate already exists
        if cert_path.exists() and key_path.exists():
            logger.info("Using existing SSL certificate")
            return str(cert_path), str(key_path)
        
        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(common_name),
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))
            ]),
            critical=False
        ).sign(key, hashes.SHA256())
        
        # Save to files
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        cert_path.chmod(0o644)
        key_path.chmod(0o600)
        
        logger.info(f"Generated SSL certificate: {cert_path}")
        return str(cert_path), str(key_path)
    
    @staticmethod
    def create_server(
        host: str,
        port: int,
        handler: BaseHTTPRequestHandler,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None
    ) -> HTTPServer:
        """
        Create HTTPS server
        
        Args:
            host: Host to bind to
            port: Port to listen on
            handler: Request handler class
            cert_path: Path to SSL certificate (auto-generated if None)
            key_path: Path to SSL private key (auto-generated if None)
            
        Returns:
            HTTPServer instance with SSL/TLS
        """
        if cert_path is None or key_path is None:
            cert_path, key_path = SecureHTTPServer.generate_self_signed_cert()
        
        httpd = HTTPServer((host, port), handler)
        
        # Wrap with SSL
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Use secure cipher suites
        context.set_ciphers(
            'ECDHE-ECDSA-AES256-GCM-SHA384:'
            'ECDHE-RSA-AES256-GCM-SHA384:'
            'ECDHE-ECDSA-AES128-GCM-SHA256:'
            'ECDHE-RSA-AES128-GCM-SHA256'
        )
        
        context.load_cert_chain(cert_path, key_path)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        
        logger.info(f"HTTPS server configured on {host}:{port}")
        return httpd
