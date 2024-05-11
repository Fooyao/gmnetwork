import asyncio, sys, random, string, time
from curl_cffi.requests import AsyncSession
from eth_account.messages import encode_defunct
from web3 import AsyncWeb3
from loguru import logger

logger.remove()
logger.add(sys.stdout, colorize=True, format="<g>{time:HH:mm:ss:SSS}</g> | <level>{message}</level>")


class redbrick:
    def __init__(self, nstproxy_Channel, nstproxy_Password, private_key):
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider('https://klaytn.api.onfinality.io/public'))
        self.client = AsyncSession(timeout=120, impersonate="chrome120")
        self.nstproxy_Channel, self.nstproxy_Password = nstproxy_Channel, nstproxy_Password
        self.account = self.w3.eth.account.from_key(private_key)
        self.starLeavel = 0

    async def init(self, state=False):
        for _ in range(3):
            if await self.login(state):
                return True
        return False

    async def login(self, state=False):
        try:
            session = ''.join(random.choices(string.digits + string.ascii_letters, k=10))
            nstproxy = f"http://{self.nstproxy_Channel}-residential-country_ANY-r_5m-s_{session}:{self.nstproxy_Password}@gw-us.nstproxy.com:24125"
            self.client = AsyncSession(timeout=120, impersonate="chrome120", proxy=nstproxy)
            timestamp = int(time.time())
            sig_msg = f"Welcome to GM Launchpad.\nPlease sign this message to login GM Launchpad.\n\nTimestamp: {timestamp}"
            signature = self.account.sign_message(encode_defunct(text=sig_msg))
            json_data = {
                "address": self.account.address,
                "message": "Welcome to GM Launchpad.\nPlease sign this message to login GM Launchpad.",
                "timestamp": timestamp,
                "signature": signature['signature'].hex()[2:],
                "login_type": 100
            }
            res = await self.client.post("https://api-launchpad.gmnetwork.ai/user/login/", json=json_data)
            if res.json()['success']:
                accessToken = res.json()['result']['access_token']
                invite_code = res.json()['result']['user_info']['invite_code']
                status = res.json()['result']['user_info']['status']
                self.client.headers.update({"Access-Token": accessToken})
                if state:
                    return True
                logger.success(f"[{self.account.address}] 登录成功")
                if status == 300:
                    await self.bindInvite()
                elif status == 100 and "token_id" not in res.json()['result']['user_info']['agent']:
                    await self.agent_set()
                else:
                    return await self.task_center()
            else:
                logger.error(f"[{self.account.address}] 登录失败")
                return False
        except Exception as e:
            logger.error(f"[{self.account.address}] 登录失败：{e}")
            return False

    async def bindInvite(self):
        try:
            json_data = {"invite_code": "GMGN", "address": self.account.address}
            res = await self.client.post("https://api-launchpad.gmnetwork.ai/user/invite_code/", json=json_data)
            if res.json()['success']:
                logger.success(f"[{self.account.address}] 绑定邀请码成功")
                return await self.agent_set()
            else:
                logger.error(f"[{self.account.address}] 绑定邀请码失败")
                return False
        except Exception as e:
            logger.error(f"[{self.account.address}] 绑定邀请码失败：{e}")
            return False

    async def agent_set(self):
        try:
            json_data = {"nft_id": ""}
            res = await self.client.post("https://api-launchpad.gmnetwork.ai/user/auth/agent_set/", json=json_data)
            if res.json()['success']:
                if "token_id" in res.json()['result']:
                    logger.success(f"[{self.account.address}] 设置代理成功")
                    return await self.task_center()
                else:
                    return await self.agent_set()
            else:
                logger.error(f"[{self.account.address}] 设置代理失败")
                return False
        except Exception as e:
            logger.error(f"[{self.account.address}] 设置代理失败：{e}")
            return False

    async def task_center(self):
        try:
            res = await self.client.get("https://api-launchpad.gmnetwork.ai/task/auth/task_center/?season_um=1")
            if res.json()['success']:
                check_in_task_info = res.json()['result']['check_in_task_info']
                last_check_in_time = check_in_task_info['last_check_in_time']
                check_in_task_info['title'] = "签到"
                if int(time.time()) - last_check_in_time > 86400:
                    check_in_task_info['task_done_time'] = 0
                else:
                    check_in_task_info['task_done_time'] = 1
                task_list = [check_in_task_info]
                task_list += res.json()['result']['launchpad_tasks_info']
                # task_list += res.json()['result']['questn_tasks_info']
                for index in range(len(task_list)):
                    task_id = task_list[index]['id']
                    task_done_time = task_list[index]['task_done_time']
                    title = task_list[index]['title']
                    if task_done_time == 0:
                        await self.task(task_id, title)
                        if index % 4 == 0 and index != 0 and index != len(task_list) - 1:
                            await self.init(True)
                            # logger.info(f"[{self.account.address}] 休息30秒")
                            # await asyncio.sleep(30)
                await self.user_energy()
                return True
            else:
                logger.error(f"[{self.account.address}] 获取任务失败")
                return False
        except Exception as e:
            logger.error(f"[{self.account.address}] 获取任务失败：{e}")
            return False

    async def task(self, task_id, title, category=100):
        if category == 100:
            info = "领取"
        else:
            info = "完成"
        try:
            json_data = {"category": category, "task_id": task_id}
            res = await self.client.post("https://api-launchpad.gmnetwork.ai/task/auth/task/", json=json_data)
            if res.status_code == 200 and res.json()['success']:
                logger.success(f"[{self.account.address}] {info}任务{title}成功")
                if category == 100:
                    return await self.task(task_id, title, 200)
                else:
                    return True
            else:
                logger.error(f"[{self.account.address}] {info}任务{title}失败")
                return False
        except Exception as e:
            logger.error(f"[{self.account.address}] {info}任务{title}失败：{e}")
            return False

    async def user_energy(self):
        try:
            res = await self.client.get("https://api-launchpad.gmnetwork.ai/energy/auth/user_energy/")
            if res.json()['success']:
                logger.success(f"[{self.account.address}] 总能量：{res.json()['result']['total']}")
                return True
            else:
                logger.error(f"[{self.account.address}] 获取能量失败")
                return False
        except Exception as e:
            logger.error(f"[{self.account.address}] 获取能量失败：{e}")
            return False


async def do(semaphore, nstproxy_Channel, nstproxy_Password, private_key):
    async with semaphore:
        await redbrick(nstproxy_Channel, nstproxy_Password, private_key).init()


async def main(file_path, semaphore, nstproxy_Channel, nstproxy_Password):
    semaphore = asyncio.Semaphore(semaphore)
    with open(file_path, 'r') as f:
        task = [do(semaphore, nstproxy_Channel, nstproxy_Password, account_line.strip().split('----')[1].strip()) for account_line in f]
    await asyncio.gather(*task)


if __name__ == '__main__':
    _nstproxy_Channel = input('请输入nstproxy_频道:').strip()
    _nstproxy_Password = input('请输入nstproxy_密码:').strip()
    _semaphore = int(input('请输入并发数:').strip())
    _file_path = input('请输入地址----私钥文件:').strip()
    asyncio.run(main(_file_path, _semaphore, _nstproxy_Channel, _nstproxy_Password))
