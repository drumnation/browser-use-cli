# -*- coding: utf-8 -*-
# @Time    : 2025/1/2
# @Author  : wenshao
# @ProjectName: browser-use-webui
# @FileName: custom_action.py

import pyperclip
from browser_use.agent.views import ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.service import Controller
from browser_use.browser.views import BrowserState


class CustomController(Controller):
    def __init__(self):
        super().__init__()
        self._register_custom_actions()

    def _register_custom_actions(self):
        """Register all custom browser actions"""

        @self.registry.action("Copy text to clipboard")
        def copy_to_clipboard(text: str):
            pyperclip.copy(text)
            return ActionResult(extracted_content=text)

        @self.registry.action("Paste text from clipboard", requires_browser=True)
        async def paste_from_clipboard(browser: BrowserContext):
            text = pyperclip.paste()
            # send text to browser
            page = await browser.get_current_page()
            await page.keyboard.type(text)

            return ActionResult(extracted_content=text)

    async def get_browser_state(self, browser_context: BrowserContext) -> BrowserState:
        """Get the current state of the browser"""
        state = await browser_context.get_state(use_vision=True)
        return state
