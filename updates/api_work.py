import asyncio
import aiohttp
import random


# пока не используется
headers = { 
    'User-Agent': random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0)",
    ])
}


# Получение актуальных версий по API
async def get_remote_versions(MOS_KEY, DATASETS):
    versions = {}
    async with aiohttp.ClientSession() as session:
        for name, dataset_id in DATASETS.items():
            while True:
                try:
                    url = f"https://apidata.mos.ru/v1/datasets/{dataset_id}/version?api_key={MOS_KEY}"
                    async with session.get(url) as response:
                        response.raise_for_status()
                        metadata = await response.json()
                        versions[name] = metadata.get("ReleaseNumber")
                        break
                except Exception as e:
                    print(f"Ошибка при получении версии {dataset_id} {name}: {e}. Повтор через 5 секунд...")
                    await asyncio.sleep(3)
    return versions


# Получение количества записей в датасете
async def get_dataset_count(MOS_KEY, session, dataset_id):
    url = f"https://apidata.mos.ru/v1/datasets/{dataset_id}/count?api_key={MOS_KEY}"
    while True:
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                count = (await response.text()).strip()
                if count: 
                    break 
        except Exception as e:
            print(f"Ошибка при получении кол-ва записей для {dataset_id}: {e}. Повтор...")
        await asyncio.sleep(3)
    return int(count)


# Получение записей датасета с параметрами top и skip
async def get_dataset_data(MOS_KEY, session, dataset_id, top, skip):
    url = f"https://apidata.mos.ru/v1/datasets/{dataset_id}/rows?api_key={MOS_KEY}&$top={top}&$skip={skip}"
    print(f"Загрузка: {url}")
    async with session.get(url, timeout=20) as response:
        print(response.status)
        response.raise_for_status()
        return await response.json()