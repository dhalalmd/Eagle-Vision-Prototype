import socket
import datetime
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import ipaddress

def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def generate_self_signed_cert(output_dir: str = "certs"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    cert_file = out_path / "cert.pem"
    key_file = out_path / "key.pem"
    
    if cert_file.exists() and key_file.exists():
        print(f"Certificates already exist in {out_path.resolve()}")
        return cert_file, key_file

    print("Generating RSA key pair...")
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    lan_ip = get_lan_ip()
    print(f"Adding Subject Alternative Names: localhost, 127.0.0.1, {lan_ip}")

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"SmartCCTV-{lan_ip}"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Smart CCTV SIH"),
    ])

    san_list = [
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]
    try:
        san_list.append(x509.IPAddress(ipaddress.ip_address(lan_ip)))
    except ValueError:
        pass

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName(san_list),
        critical=False,
    ).sign(key, hashes.SHA256())

    with open(key_file, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Self-signed certificate generated at:\n  Cert: {cert_file.resolve()}\n  Key:  {key_file.resolve()}")
    return cert_file, key_file

if __name__ == "__main__":
    generate_self_signed_cert()
