"""Configuração e nomes canônicos da arquitetura multi-rede.

O navegador escolhe um ``realm_id`` conhecido pela aplicação. Endereços RPC e
ZMQ nunca são aceitos a partir de requisições: cada ingestor recebe sua origem
exclusivamente por variáveis de ambiente do serviço Docker.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

REALM_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


class BitcoinNetwork(StrEnum):
    """Redes Bitcoin suportadas pelo projeto."""

    REGTEST = "regtest"
    SIGNET = "signet"
    MAINNET = "mainnet"

    @property
    def rpc_chain(self) -> str:
        """Retorna o nome usado por ``getblockchaininfo.chain``."""
        return "main" if self is BitcoinNetwork.MAINNET else self.value

    @classmethod
    def parse(cls, value: str) -> BitcoinNetwork:
        """Normaliza o alias ``main`` e valida a rede informada."""
        normalized = value.strip().lower()
        if normalized == "main":
            normalized = cls.MAINNET.value
        return cls(normalized)


@dataclass(frozen=True, slots=True)
class NetworkDefinition:
    """Metadado público e estável de uma arena de jogo."""

    realm_id: str
    network: BitcoinNetwork
    node_id: str
    label: str
    optional: bool = False

    @property
    def chain(self) -> str:
        """Nome canônico da chain retornado pelo Bitcoin Core."""
        return self.network.rpc_chain


NETWORK_CATALOG: tuple[NetworkDefinition, ...] = (
    NetworkDefinition("regtest", BitcoinNetwork.REGTEST, "regtest-local", "Regtest local"),
    NetworkDefinition("signet", BitcoinNetwork.SIGNET, "signet-public", "Signet pública"),
    NetworkDefinition(
        "mainnet",
        BitcoinNetwork.MAINNET,
        "mainnet-pruned",
        "Mainnet podada",
        optional=True,
    ),
)
NETWORKS_BY_REALM = {definition.realm_id: definition for definition in NETWORK_CATALOG}


def validate_id_format(value: str) -> str:
    """Valida um identificador (realm_id ou node_id) antes de usá-lo em canais ou chaves Redis.

    O pattern ``^[a-z0-9][a-z0-9_-]{0,31}$`` é compartilhado entre realm_id e node_id
    para manter consistência nos namespaces Redis.
    """
    normalized = value.strip().lower()
    if not REALM_ID_PATTERN.fullmatch(normalized):
        raise ValueError("ID inválido")
    return normalized


# Alias para compatibilidade — nome mais semântico para o contexto de realm.
validate_realm_id = validate_id_format


def default_realm_id() -> str:
    """Obtém o realm padrão e impede fallback silencioso para valor desconhecido."""
    realm_id = validate_realm_id(os.getenv("DEFAULT_REALM_ID", "regtest"))
    if realm_id not in NETWORKS_BY_REALM:
        raise RuntimeError(f"DEFAULT_REALM_ID não suportado: {realm_id}")
    return realm_id


def required_environment(name: str) -> str:
    """Obtém uma variável obrigatória sem introduzir credenciais padrão."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


def read_secret(variable_name: str, file_variable_name: str) -> str:
    """Lê um segredo por arquivo quando configurado, com fallback para ambiente."""
    secret_path = os.getenv(file_variable_name)
    if secret_path:
        try:
            value = Path(secret_path).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeError(f"Não foi possível ler {file_variable_name}") from exc
        if not value:
            raise RuntimeError(f"Arquivo indicado por {file_variable_name} está vazio")
        return value
    return required_environment(variable_name)


@dataclass(frozen=True, slots=True)
class NodeConfig:
    """Configuração privada de um processo ingestor e sua origem Bitcoin Core."""

    node_id: str
    realm_id: str
    network: BitcoinNetwork
    rpc_host: str
    rpc_port: int
    zmq_host: str
    zmq_port: int
    rpc_user: str
    rpc_password: str
    game_mode: str = "mempool"
    high_fee_rate_sat_vb: float = 20.0
    queue_max_size: int = 5000
    process_interval_seconds: float = 0.01

    def __post_init__(self) -> None:
        """Recusa IDs e portas que poderiam corromper roteamento ou namespace.

        Validações:
        - ``realm_id`` é normalizado e validado contra o catálogo.
        - ``network`` deve corresponder ao ``realm_id``.
        - ``node_id`` deve corresponder ao catálogo e seguir o pattern.
        - Portas RPC e ZMQ devem estar em ``1..65535``.
        - ``queue_max_size`` e ``process_interval_seconds`` devem ser positivos.

        Raises:
            ValueError: Se qualquer validação falhar.
        """
        normalized_realm = validate_realm_id(self.realm_id)
        object.__setattr__(self, "realm_id", normalized_realm)
        definition = NETWORKS_BY_REALM.get(normalized_realm)
        if definition is None:
            raise ValueError(f"REALM_ID não suportado: {normalized_realm}")
        if definition.network is not self.network:
            raise ValueError(
                f"REALM_ID {normalized_realm} não pertence à rede {self.network.value}"
            )
        if self.node_id != definition.node_id:
            raise ValueError(f"NODE_ID {self.node_id} diverge do catálogo para {normalized_realm}")
        if not REALM_ID_PATTERN.fullmatch(self.node_id):
            raise ValueError("NODE_ID inválido")
        for name, port in (("RPC_PORT", self.rpc_port), ("ZMQ_PORT", self.zmq_port)):
            if not 0 < port <= 65535:
                raise ValueError(f"{name} inválida")
        if self.queue_max_size <= 0:
            raise ValueError("TX_QUEUE_MAX_SIZE deve ser positivo")
        if self.process_interval_seconds <= 0:
            raise ValueError("TX_PROCESS_INTERVAL_SECONDS deve ser positivo")

    @property
    def rpc_url(self) -> str:
        """URL RPC interna do nó, nunca exposta no catálogo HTTP."""
        return f"http://{self.rpc_host}:{self.rpc_port}"

    @property
    def zmq_url(self) -> str:
        """URL ZMQ interna do nó."""
        return f"tcp://{self.zmq_host}:{self.zmq_port}"

    @classmethod
    def from_environment(cls) -> NodeConfig:
        """Carrega a configuração service-local do ingestor atual.

        Lê variáveis de ambiente e aplica defaults baseados na rede.
        ``RPC_USER`` e ``RPC_PASSWORD`` são obrigatórios.

        Returns:
            Instância de ``NodeConfig`` validada.

        Raises:
            RuntimeError: Se ``RPC_USER`` ou ``RPC_PASSWORD`` estiverem ausentes.
            ValueError: Se ``REALM_ID`` ou ``NODE_ID`` forem inválidos.
        """
        network = BitcoinNetwork.parse(os.getenv("BITCOIN_NETWORK", "regtest"))
        realm_id = validate_realm_id(os.getenv("REALM_ID", network.value))
        default_ports = {
            BitcoinNetwork.REGTEST: 18443,
            BitcoinNetwork.SIGNET: 38332,
            BitcoinNetwork.MAINNET: 8332,
        }
        node_id = os.getenv("NODE_ID", NETWORKS_BY_REALM.get(realm_id, NETWORKS_BY_REALM["regtest"]).node_id).strip().lower()
        return cls(
            node_id=node_id,
            realm_id=realm_id,
            network=network,
            rpc_host=os.getenv("RPC_HOST", f"bitcoin-{realm_id}"),
            rpc_port=int(os.getenv("RPC_PORT", str(default_ports[network]))),
            zmq_host=os.getenv("ZMQ_HOST", f"bitcoin-{realm_id}"),
            zmq_port=int(os.getenv("ZMQ_PORT", "28332")),
            rpc_user=required_environment("RPC_USER"),
            rpc_password=read_secret("RPC_PASSWORD", "RPC_PASSWORD_FILE"),
            game_mode=os.getenv("GAME_MODE", "mempool"),
            high_fee_rate_sat_vb=float(os.getenv("HIGH_FEE_RATE_SAT_VB", "20")),
            queue_max_size=int(os.getenv("TX_QUEUE_MAX_SIZE", "5000")),
            process_interval_seconds=float(os.getenv("TX_PROCESS_INTERVAL_SECONDS", "1.0")),
        )
