import asyncio
import aiohttp
import ssl
import base64
import psutil
import re
from logger import logger
from exceptions import LeagueClientError

class LeagueClient:
    def __init__(self):
        self.port = None
        self.token = None
        self.session = None
        self.base_url = None
        self._discover_lcu()
        logger.info("LeagueClient (direct LCU API) initialized")

    def _discover_lcu(self):
        # Find the LeagueClientUx process and extract port/token
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['name'] and 'LeagueClientUx' in proc.info['name']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    port_match = re.search(r'--app-port=(\d+)', cmdline)
                    token_match = re.search(r'--remoting-auth-token=([\w-]+)', cmdline)
                    if port_match and token_match:
                        self.port = port_match.group(1)
                        self.token = token_match.group(1)
                        self.base_url = f'https://127.0.0.1:{self.port}'
                        logger.info(f"Discovered LCU API at port {self.port}")
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        logger.error("Could not find LeagueClientUx process or extract port/token.")
        raise LeagueClientError("Could not find LeagueClientUx process or extract port/token.")

    async def _get_session(self):
        if self.session is None:
            auth = base64.b64encode(f"riot:{self.token}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth}',
                'Accept': 'application/json',
            }
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            self.session = aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(ssl=ssl_ctx))
        return self.session

    async def get_champion_select_session(self):
        try:
            session = await self._get_session()
            url = f'{self.base_url}/lol-champ-select/v1/session'
            async with session.get(url) as resp:
                if resp.status == 200:
                    logger.debug("Successfully fetched champion select session from LCU API")
                    return await resp.json()
                else:
                    logger.error(f"Failed to fetch champion select session: {resp.status}")
                    raise LeagueClientError(f"Failed to fetch champion select session: {resp.status}")
        except Exception as e:
            logger.error(f"Error getting champion select session: {str(e)}", exc_info=True)
            raise LeagueClientError(f"Failed to get champion select session: {str(e)}")

    async def get_enemy_champions(self):
        try:
            session = await self.get_champion_select_session()
            if not session:
                return []
            enemy_champions = []
            my_team = None
            for player in session['myTeam']:
                if player.get('cellId') == session.get('localPlayerCellId'):
                    my_team = 'myTeam'
                    break
            if my_team is None:
                my_team = 'theirTeam'
            enemy_team = 'theirTeam' if my_team == 'myTeam' else 'myTeam'
            for player in session[enemy_team]:
                if player.get('championId') and player['championId'] != 0:
                    champ_id = player['championId']
                    champ_data = await self.get_champion_data(champ_id)
                    if champ_data and 'name' in champ_data:
                        enemy_champions.append(champ_data['name'])
            return enemy_champions
        except Exception as e:
            logger.error(f"Error getting enemy champions: {str(e)}", exc_info=True)
            raise LeagueClientError(f"Failed to get enemy champions: {str(e)}")

    async def get_champion_data(self, champion_id):
        try:
            session = await self._get_session()
            url = f'{self.base_url}/lol-champions/v1/champions/{champion_id}'
            async with session.get(url) as resp:
                if resp.status == 200:
                    logger.debug(f"Successfully fetched champion data for ID {champion_id} from LCU API")
                    return await resp.json()
                else:
                    logger.error(f"Failed to fetch champion data: {resp.status}")
                    raise LeagueClientError(f"Failed to fetch champion data: {resp.status}")
        except Exception as e:
            logger.error(f"Error getting champion data: {str(e)}", exc_info=True)
            raise LeagueClientError(f"Failed to get champion data: {str(e)}")

    async def get_gameflow_phase(self):
        try:
            session = await self._get_session()
            url = f'{self.base_url}/lol-gameflow/v1/session'
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    phase = data.get('phase', None)
                    logger.debug(f"Current gameflow phase: {phase}")
                    return phase
                else:
                    logger.error(f"Failed to fetch gameflow phase: {resp.status}")
                    raise LeagueClientError(f"Failed to fetch gameflow phase: {resp.status}")
        except Exception as e:
            logger.error(f"Error getting gameflow phase: {str(e)}", exc_info=True)
            raise LeagueClientError(f"Failed to get gameflow phase: {str(e)}")

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None 