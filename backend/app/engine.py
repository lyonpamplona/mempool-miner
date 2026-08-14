"""Motor de metadados de transações e integração RPC com o Bitcoin Core."""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mnemonic import Mnemonic

logger = logging.getLogger(__name__)
load_dotenv()


def required_environment(name: str) -> str:
    """Obtém uma variável obrigatória sem introduzir credenciais padrão."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


class GameEngine:
    """Converte transações em palavras e consulta metadados no Bitcoin Core."""

    def __init__(self) -> None:
        """Carrega a rede, as credenciais RPC e os parâmetros da mecânica."""
        self.network = os.getenv("BITCOIN_NETWORK", "regtest").lower()
        self.game_mode = os.getenv("GAME_MODE", "mempool")
        self.mnemo = Mnemonic("english")

        self.rpc_user = required_environment("RPC_USER")
        self.rpc_password = required_environment("RPC_PASSWORD")
        self.rpc_host = os.getenv("RPC_HOST", "bitcoind")
        self.rpc_port = os.getenv("RPC_PORT", "18443")
        self.rpc_url = f"http://{self.rpc_host}:{self.rpc_port}"
        self.high_fee_rate = float(os.getenv("HIGH_FEE_RATE_SAT_VB", "20"))

        auth = f"{self.rpc_user}:{self.rpc_password}".encode()
        token = base64.b64encode(auth).decode()
        self.auth_header = {"Authorization": f"Basic {token}"}
        self.http_client = httpx.AsyncClient(timeout=2.0)

    def tx_to_word(self, txid: str) -> str:
        """Deriva uma palavra BIP39 determinística dos primeiros 128 bits do TXID.

        Em caso de TXID inválido, devolve BITCOIN para manter o fluxo do jogo
        operacional sem propagar dados sensíveis ou detalhes internos ao cliente.
        """
        try:
            if len(txid) < 32:
                raise ValueError("TXID curto demais para gerar entropia BIP39")
            entropy = bytes.fromhex(txid[:32])
            return self.mnemo.to_mnemonic(entropy).split()[0].upper()
        except (ValueError, IndexError):
            logger.warning("TXID inválido recebido para conversão em palavra")
            return "BITCOIN"

    async def _rpc_call(self, method: str, params: list[Any]) -> Any:
        """Executa uma chamada JSON-RPC e retorna apenas o campo result.

        None é retornado quando o nó está indisponível, responde com erro ou
        devolve um documento inválido. A falha fica registrada no log do serviço.
        """
        payload = {
            "jsonrpc": "1.0",
            "id": "mempool_miner",
            "method": method,
            "params": params,
        }

        try:
            response = await self.http_client.post(
                self.rpc_url,
                headers=self.auth_header,
                json=payload,
            )
            response.raise_for_status()
            document = response.json()
            if document.get("error"):
                logger.warning("Bitcoin RPC %s retornou erro: %s", method, document["error"])
                return None
            return document.get("result")
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("Falha na chamada Bitcoin RPC %s: %s", method, exc)
            return None

    async def get_tx_metadata(self, txid: str) -> dict[str, Any]:
        """Obtém palavra, raridade, taxa efetiva e tamanho virtual da transação."""
        is_golden = txid.startswith("00")
        is_high_fee = False
        vsize = 250
        fee_rate_sat_vb = 0.0

        result = await self._rpc_call("getmempoolentry", [txid])
        if isinstance(result, dict):
            candidate_vsize = result.get("vsize", vsize)
            if isinstance(candidate_vsize, (int, float)) and candidate_vsize > 0:
                vsize = int(candidate_vsize)

            fees = result.get("fees", {})
            base_fee_btc = fees.get("base", 0) if isinstance(fees, dict) else 0
            if isinstance(base_fee_btc, (int, float)):
                fee_rate_sat_vb = (float(base_fee_btc) * 100_000_000) / vsize
                is_high_fee = fee_rate_sat_vb >= self.high_fee_rate

        return {
            "word": self.tx_to_word(txid),
            "is_golden": is_golden,
            "is_high_fee": is_high_fee,
            "vsize": vsize,
            "fee_rate_sat_vb": round(fee_rate_sat_vb, 2),
        }

    async def get_mempool_size(self) -> int | None:
        """Retorna o total informado pelo nó ou None quando o RPC falha."""
        result = await self._rpc_call("getmempoolinfo", [])
        if not isinstance(result, dict):
            return None
        size = result.get("size")
        return int(size) if isinstance(size, (int, float)) and size >= 0 else None

    async def close(self) -> None:
        """Libera o pool HTTP utilizado nas chamadas RPC."""
        await self.http_client.aclose()
