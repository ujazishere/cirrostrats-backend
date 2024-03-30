# from dj.dj_app.root.root_class import Root_class      # this works in jupyter interactive
from root_class import Root_class
import pickle
import asyncio,aiohttp
# this function pulls all datis and returns them in list form
all_datis_airports_path = r'c:\users\ujasv\onedrive\desktop\codes\cirrostrats\all_datis_airports.pkl'
with open(all_datis_airports_path, 'rb') as f:
    all_datis_airports = pickle.load(f)

# Read this for async chat https://chat.openai.com/share/24a00dc6-1293-4263-9c11-0c2b188c0f7a
async def get_tasks(session):
    tasks = []
    for airport_id in all_datis_airports:
        url = f"https://datis.clowd.io/api/{airport_id}"
        tasks.append(asyncio.create_task(session.get(url)))
    return tasks

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = await get_tasks(session)
        # Upto here the tasks are created which is very light.

        # Actual pull work is done using as_completed 
        datis_resp = []
        for resp in asyncio.as_completed(tasks):        # use .gather() instead of .as_completed for background completion
            resp = await resp           # Necessary operation. Have to await it to get results.
            jj = await resp.json()
            datis_raw = 'n/a'
            if type(jj) == list and 'datis' in jj[0].keys():
                datis_raw = jj[0]['datis']
            datis_resp.append(datis_raw)
        return datis_resp

# This .run() works here but wont work in jupyter interactive. 
    # in interactive use .ensure_future instead of .run and await it:
        # all_76_datis = await asyncio.ensure_future(main()) 
if __name__ == "__main__":
    all_76_datis = asyncio.run(main())



# extract datis with dates in the filename
yyyymmddhhmm = Root_class().date_time(raw_utc='HM')
path = rf'c:\users\ujasv\onedrive\desktop\pickles\datis_info_stack_{yyyymmddhhmm}.pkl'
print('totals:', len(all_76_datis),)
print('saving it here:', path,)
print('example:', all_76_datis[0])

# **********CAUTION!!! HARD WRITE***************
with open(path, 'wb') as f:
    pickle.dump(all_76_datis,f)
