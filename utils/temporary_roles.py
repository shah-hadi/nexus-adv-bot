import asyncio
import json
import time
from pathlib import Path

import discord


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "temporary_roles.json"


class TemporaryRoleManager:
    def __init__(self, bot):
        self.bot = bot
        self.records = self._load()
        self.tasks = {}
        self.restore_task = None

    @staticmethod
    def key(guild_id: int, member_id: int, role_id: int) -> str:
        return f"{guild_id}:{member_id}:{role_id}"

    def _load(self) -> dict:
        if not DATA_PATH.exists():
            return {}
        try:
            with DATA_PATH.open(encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save(self) -> None:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = DATA_PATH.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(self.records, file, indent=2)
            file.write("\n")
        temporary.replace(DATA_PATH)

    def start(self) -> None:
        if not self.restore_task:
            self.restore_task = asyncio.create_task(self._restore())

    def stop(self) -> None:
        if self.restore_task:
            self.restore_task.cancel()
        for task in self.tasks.values():
            task.cancel()
        self.tasks.clear()

    def is_tracked(self, guild_id: int, member_id: int, role_id: int) -> bool:
        return self.key(guild_id, member_id, role_id) in self.records

    async def assign(self, guild_id: int, member_id: int, role_id: int, duration: int) -> int:
        key = self.key(guild_id, member_id, role_id)
        expires_at = int(time.time()) + duration
        record = {
            "guild_id": guild_id,
            "member_id": member_id,
            "role_id": role_id,
            "expires_at": expires_at,
        }
        old_task = self.tasks.pop(key, None)
        if old_task:
            old_task.cancel()
        self.records[key] = record
        self._save()
        self.tasks[key] = asyncio.create_task(self._expire(key, record))
        return expires_at

    async def _restore(self) -> None:
        await self.bot.wait_until_ready()
        for key, record in list(self.records.items()):
            self.tasks[key] = asyncio.create_task(self._expire(key, record))

    async def _expire(self, key: str, record: dict) -> None:
        delay = max(0, record["expires_at"] - int(time.time()))
        await asyncio.sleep(delay)
        if self.records.get(key) != record:
            return
        try:
            guild = self.bot.get_guild(record["guild_id"])
            if guild:
                role = guild.get_role(record["role_id"])
                member = guild.get_member(record["member_id"])
                if member is None:
                    try:
                        member = await guild.fetch_member(record["member_id"])
                    except (discord.NotFound, discord.HTTPException):
                        member = None
                if member and role and role in member.roles:
                    await member.remove_roles(role, reason="Temporary role expired")
        except discord.HTTPException:
            pass
        finally:
            if self.records.get(key) == record:
                self.records.pop(key, None)
                self.tasks.pop(key, None)
                self._save()
