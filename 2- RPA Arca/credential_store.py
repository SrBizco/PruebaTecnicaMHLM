"""Windows Credential Manager adapter for optional ARCA profiles.

Profile metadata and passwords use separate generic credentials. Listing the
profiles therefore does not enumerate or load any password blobs.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sys
from typing import Any
from uuid import uuid4


PROFILE_PREFIX = "PruebaTecnicaMHLM/ARCA/Profile/"
SECRET_PREFIX = "PruebaTecnicaMHLM/ARCA/Secret/"
_CUIT_RE = re.compile(r"^\d{11}$")


class CredentialStoreError(Exception):
    """Safe-to-display credential-store error; never contains secret data."""


@dataclass(frozen=True)
class Profile:
    profile_id: str
    label: str
    cuit: str

    @property
    def display_name(self) -> str:
        return f"{self.label} — CUIT terminada en {self.cuit[-4:]} · {self.profile_id[:8]}"


def _win32cred():
    if sys.platform != "win32":
        raise CredentialStoreError("Los perfiles guardados solo están disponibles en Windows.")
    try:
        import win32cred
    except ImportError as exc:
        raise CredentialStoreError(
            "No está disponible pywin32. Reinstala las dependencias del proyecto."
        ) from exc
    return win32cred


def _generic_credential(target: str, blob: str, comment: str, username: str = "") -> dict[str, Any]:
    win32cred = _win32cred()
    return {
        "Type": win32cred.CRED_TYPE_GENERIC,
        "TargetName": target,
        "CredentialBlob": blob,
        "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
        "UserName": username,
        "Comment": comment[:256],
        "Flags": 0,
        "Attributes": [],
    }


def _blob_to_text(blob: Any) -> str:
    if isinstance(blob, str):
        return blob
    if isinstance(blob, bytes):
        try:
            return blob.decode("utf-16-le").rstrip("\x00")
        except UnicodeDecodeError as exc:
            raise CredentialStoreError("Windows devolvió un dato de perfil ilegible.") from exc
    raise CredentialStoreError("Windows devolvió un dato de perfil en un formato inesperado.")


def _read_profile_metadata(credential: dict[str, Any]) -> Profile | None:
    target = credential.get("TargetName", "")
    if not target.startswith(PROFILE_PREFIX):
        return None
    profile_id = target[len(PROFILE_PREFIX) :]
    try:
        data = json.loads(_blob_to_text(credential.get("CredentialBlob", "")))
        label = data["label"]
        cuit = data["cuit"]
    except (CredentialStoreError, TypeError, ValueError, KeyError):
        return None
    if not isinstance(label, str) or not isinstance(cuit, str) or not _CUIT_RE.fullmatch(cuit):
        return None
    if not label.strip() or len(profile_id) != 32:
        return None
    return Profile(profile_id=profile_id, label=label, cuit=cuit)


def list_profiles() -> list[Profile]:
    """List metadata only; never reads the separate password credentials."""
    win32cred = _win32cred()
    from pywintypes import error as WindowsCredentialError

    try:
        credentials = win32cred.CredEnumerate(PROFILE_PREFIX + "*", 0)
    except WindowsCredentialError as exc:
        # ERROR_NOT_FOUND is the normal state before the first profile is added.
        if getattr(exc, "winerror", None) == 1168:
            return []
        raise CredentialStoreError("No se pudieron consultar los perfiles de Windows.") from exc

    profiles = [profile for item in credentials if (profile := _read_profile_metadata(item))]
    return sorted(profiles, key=lambda profile: (profile.label.casefold(), profile.cuit))


def save_profile(label: str, cuit: str, password: str) -> Profile:
    """Persist a profile directly in the current user's Windows credential vault."""
    win32cred = _win32cred()
    label = label.strip()
    cuit = cuit.strip()
    if not label or len(label) > 60:
        raise CredentialStoreError("El nombre del perfil debe tener entre 1 y 60 caracteres.")
    if not _CUIT_RE.fullmatch(cuit):
        raise CredentialStoreError("La CUIT debe contener exactamente 11 dígitos.")
    if not password:
        raise CredentialStoreError("La clave no puede estar vacía.")

    profile_id = uuid4().hex
    profile = Profile(profile_id=profile_id, label=label, cuit=cuit)
    secret_target = SECRET_PREFIX + profile_id
    metadata_target = PROFILE_PREFIX + profile_id

    metadata = json.dumps({"label": label, "cuit": cuit}, ensure_ascii=False)
    try:
        win32cred.CredWrite(
            _generic_credential(
                metadata_target,
                metadata,
                "Metadatos de perfil ARCA; no contiene la clave",
            ),
            0,
        )
        win32cred.CredWrite(
            _generic_credential(
                secret_target,
                password,
                "Clave fiscal ARCA; administrada por PruebaTecnicaMHLM",
                username=cuit,
            ),
            0,
        )
    except Exception as exc:
        try:
            win32cred.CredDelete(metadata_target, win32cred.CRED_TYPE_GENERIC, 0)
        except Exception:
            pass
        raise CredentialStoreError(
            "Windows no pudo guardar el perfil completo. Revisa Credential Manager por si quedó un perfil incompleto."
        ) from exc
    return profile


def get_password(profile: Profile) -> str:
    """Read only the selected profile's secret into memory for the login flow."""
    win32cred = _win32cred()
    try:
        credential = win32cred.CredRead(
            SECRET_PREFIX + profile.profile_id, win32cred.CRED_TYPE_GENERIC, 0
        )
    except Exception as exc:
        raise CredentialStoreError(
            "No se pudo recuperar la clave de este perfil. Revisa o elimina el perfil."
        ) from exc
    try:
        password = _blob_to_text(credential.get("CredentialBlob"))
    except CredentialStoreError:
        raise
    if not password:
        raise CredentialStoreError("El perfil seleccionado no contiene una clave válida.")
    return password


def delete_profile(profile: Profile) -> None:
    """Delete the selected password and metadata from Windows Credential Manager."""
    win32cred = _win32cred()
    from pywintypes import error as WindowsCredentialError

    try:
        win32cred.CredDelete(SECRET_PREFIX + profile.profile_id, win32cred.CRED_TYPE_GENERIC, 0)
    except WindowsCredentialError as exc:
        # Keep metadata visible if deleting the actual secret failed for any reason other than absence.
        if getattr(exc, "winerror", None) != 1168:
            raise CredentialStoreError(
                "No se pudo eliminar la clave guardada en Windows; el perfil sigue visible para reintentar."
            ) from exc
    try:
        win32cred.CredDelete(PROFILE_PREFIX + profile.profile_id, win32cred.CRED_TYPE_GENERIC, 0)
    except WindowsCredentialError as exc:
        if getattr(exc, "winerror", None) == 1168:
            return
        raise CredentialStoreError(
            "Se eliminó la clave, pero Windows no pudo eliminar los metadatos del perfil. Actualiza e inténtalo otra vez."
        ) from exc
