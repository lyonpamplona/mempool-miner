"""Pacote principal do Backend para o Mempool Miner.

Módulos:
- ``engine``: Motor de metadados e integração RPC com Bitcoin Core.
- ``ingestor``: Ingestor singleton por realm (ZMQ, fila, epoch, lease).
- ``blockchain``: Cliente ZMQ assíncrono para ``rawtx`` e ``hashblock``.
- ``config``: Configuração e catálogo de redes multi-rede.
- ``storage``: Chaves Redis namespaced e migração de dados legados.
- ``events``: Contratos internos e públicos dos eventos Bitcoin.
- ``main``: API FastAPI multi-rede (REST + WebSocket).
- ``ingestor_healthcheck``: Healthcheck do ingestor (token, heartbeat, lease).
"""
