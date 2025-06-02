import asyncio, os, time, queue, threading, multiprocessing as mp
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
import psycopg2
import asyncpg
import aiohttp
import matplotlib.pyplot as plt

PG_OPTS = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', '5432')),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', 'postgres'),
    'database': os.getenv('PGDATABASE', 'postgres'),
}

def parse_name_and_desc(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, 'html.parser')
    name = ''
    h2 = soup.find('h2', class_='okved_h2_title')
    if h2 and h2.text:
        name = h2.text.strip()
    desc = ''
    div = soup.find('div', class_='okved_desc')
    if div:
        desc = ' '.join(p.get_text(strip=True) for p in div.find_all('p')).strip()
    if not name:
        name = soup.title.string.strip() if soup.title and soup.title.string else ''
    if not desc:
        meta = soup.find('meta', attrs={'name': 'description'})
        desc = meta['content'].strip() if meta and meta.get('content') else name
    return name, desc

def insert_category(cur, name: str, description: str) -> None:
    cur.execute(
        'INSERT INTO categories(name, description) VALUES (%s, %s) '
        'ON CONFLICT (name) DO NOTHING;',
        (name, description),
    )

def parse_and_save_sync(url: str) -> None:
    html = requests.get(url, timeout=15).text
    name, desc = parse_name_and_desc(html)
    with psycopg2.connect(**PG_OPTS) as conn:
        with conn.cursor() as cur:
            insert_category(cur, name, desc)
        conn.commit()

async def insert_category_async(conn: asyncpg.Connection, name: str, description: str) -> None:
    await conn.execute(
        'INSERT INTO categories(name, description) VALUES($1, $2) '
        'ON CONFLICT (name) DO NOTHING;',
        name,
        description,
    )

async def parse_and_save_async(url: str, pool: asyncpg.Pool, session: aiohttp.ClientSession, sem: asyncio.Semaphore) -> None:
    async with sem:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            resp.raise_for_status()
            html = await resp.text()
    name, desc = parse_name_and_desc(html)
    async with pool.acquire() as conn:
        await insert_category_async(conn, name, desc)

class ThreadingParser:
    def __init__(self, urls: List[str]) -> None:
        self.urls = urls
    def run(self) -> float:
        q: queue.Queue[str] = queue.Queue()
        for u in self.urls:
            q.put(u)
        def worker():
            while True:
                try:
                    u = q.get_nowait()
                except queue.Empty:
                    break
                parse_and_save_sync(u)
                q.task_done()
        threads = [threading.Thread(target=worker) for _ in range(min(20, len(self.urls)))]
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return time.perf_counter() - start

class MultiprocessingParser:
    def __init__(self, urls: List[str]) -> None:
        self.urls = urls
    def run(self) -> float:
        start = time.perf_counter()
        with mp.Pool(processes=min(mp.cpu_count(), len(self.urls))) as pool:
            pool.map(parse_and_save_sync, self.urls)
        return time.perf_counter() - start

class AsyncioParser:
    def __init__(self, urls: List[str]) -> None:
        self.urls = urls
    async def _runner(self) -> None:
        pool = await asyncpg.create_pool(min_size=1, max_size=10, **PG_OPTS)
        sem = asyncio.Semaphore(10)
        async with aiohttp.ClientSession() as session:
            tasks = [parse_and_save_async(u, pool, session, sem) for u in self.urls]
            await asyncio.gather(*tasks)
        await pool.close()
    def run(self) -> float:
        start = time.perf_counter()
        asyncio.run(self._runner())
        return time.perf_counter() - start

def benchmark(parser_cls, urls: List[str]) -> float:
    return parser_cls(urls).run()

if __name__ == '__main__':
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    );
    """

    with psycopg2.connect(**PG_OPTS) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
        conn.commit()

    URLS = [
        'https://assistentus.ru/okved/razdel-a/',
        'https://assistentus.ru/okved/razdel-b/',
        'https://assistentus.ru/okved/razdel-c/',
        'https://assistentus.ru/okved/razdel-d/',
        'https://assistentus.ru/okved/razdel-e/',
        'https://assistentus.ru/okved/razdel-f/',
        'https://assistentus.ru/okved/razdel-g/',
        'https://assistentus.ru/okved/razdel-h/',
        'https://assistentus.ru/okved/razdel-i/',
        'https://assistentus.ru/okved/razdel-j/',
        'https://assistentus.ru/okved/razdel-k/',
        'https://assistentus.ru/okved/razdel-l/',
        'https://assistentus.ru/okved/razdel-m/',
        'https://assistentus.ru/okved/razdel-n/',
        'https://assistentus.ru/okved/razdel-o/',
        'https://assistentus.ru/okved/razdel-p/',
        'https://assistentus.ru/okved/razdel-q/',
        'https://assistentus.ru/okved/razdel-r/',
    ]
    strategies = [
        ('Threading', ThreadingParser),
        ('Multiprocessing', MultiprocessingParser),
        ('Asyncio', AsyncioParser),
    ]
    names = []
    durations = []
    for label, cls in strategies:
        d = benchmark(cls, URLS)
        names.append(label)
        durations.append(d)
        print(f'{label}: {d:.2f}s')
    plt.figure(figsize=(6, 4))
    plt.bar(names, durations)
    plt.ylabel('Seconds')
    plt.title('Parsing durations by strategy')
    for i, v in enumerate(durations):
        plt.text(i, v + 0.02 * max(durations), f'{v:.2f}s', ha='center')
    out_file = f'durations.png'
    plt.tight_layout()
    plt.savefig(out_file, dpi=150, bbox_inches='tight')
    print(f'Saved performance graph to {out_file}')
