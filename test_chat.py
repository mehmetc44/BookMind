import asyncio
import sys
import time
from bookmind.graph import stream_chat_graph

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


async def main():
    prompt = "2+2 kaçtır? Sadece cevabı ver."
    print(f"Soru: {prompt}\n")
    print("Chat LangGraph Akışı (Canlı Streaming):\n")

    t0 = time.time()
    first_token_time = None

    async for chunk in stream_chat_graph(prompt):
        if chunk:
            if first_token_time is None:
                first_token_time = time.time() - t0
            sys.stdout.write(chunk)
            sys.stdout.flush()

    total_time = time.time() - t0
    print("\n")
    print("--------------------------------------------------")
    if first_token_time:
        print(f"⚡ İlk Kelime Düşme Süresi (TTFT): {first_token_time:.2f} saniye")
    print(f"⏱️  Toplam Yanıt Süresi          : {total_time:.2f} saniye")
    print("--------------------------------------------------")


if __name__ == "__main__":
    asyncio.run(main())
