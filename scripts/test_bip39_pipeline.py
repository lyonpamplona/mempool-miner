"""Teste do pipeline BIP39: envia TX no regtest e escuta eventos no Redis."""
import json
import subprocess
import time

import redis

r = redis.Redis(host="redis", port=6379, db=0, password="unlocker", decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("mempool_miner:v2:{regtest}:events")
print("Escutando canal de eventos regtest por 30s...")

# Envia 3 transações no regtest via RPC
ADDR = subprocess.run(
    ["docker", "compose", "exec", "-T", "bitcoin-regtest", "bitcoin-cli",
     "-regtest", "-rpcuser=mempool_regtest", "-rpcpassword=Nakamoto1",
     "-rpcport=18443", "-rpcwallet=miner", "getnewaddress"],
    capture_output=True, text=True, check=True,
).stdout.strip()
print(f"Endereço: {ADDR}")

time.sleep(1)
for i in range(3):
    txid = subprocess.run(
        ["docker", "compose", "exec", "-T", "bitcoin-regtest", "bitcoin-cli",
         "-regtest", "-rpcuser=mempool_regtest", "-rpcpassword=Nakamoto1",
         "-rpcport=18443", "-rpcwallet=miner", "sendtoaddress", ADDR, "0.002"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"TX {i+1} enviada: {txid}")
    time.sleep(1)

end = time.time() + 30
count = 0
while time.time() < end:
    msg = pubsub.get_message(timeout=1.0)
    if msg and msg["type"] == "message":
        count += 1
        try:
            data = json.loads(msg["data"])
            print(
                f"[{count}] action={data.get('action')} word={data.get('word')} "
                f"golden={data.get('is_golden')} high_fee={data.get('is_high_fee')} "
                f"vsize={data.get('vsize')} multiplier={data.get('multiplier')}"
            )
        except Exception:
            print(f"[{count}] {str(msg['data'])[:150]}")

print(f"Total: {count} eventos em 30s")
