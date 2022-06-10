import json
import logging
import time
from functools import cmp_to_key
from pathlib import Path

from deepl import Translator, DeepLException, Formality
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, SystemExitEvent, PreferencesUpdateEvent, \
    PreferencesEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from xdg.BaseDirectory import xdg_data_home

LOGGER = logging.getLogger(__name__)


class DeepLExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(SystemExitEvent, SystemExitEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterListener())

        data_folder = Path(xdg_data_home) / 'ulauncher-deepl'
        if data_folder.is_file():
            raise IOError(f'"{str(data_folder)}" is a file.')
        if not data_folder.exists():
            data_folder.mkdir()

        self.data_file = data_folder / 'data.json'
        self.data = json.load(self.data_file.open('r')) if self.data_file.exists() else {}
        self.translator = None

        self.source_languages = None
        self.target_languages = None
        self.last_source_language_fetch = 0
        self.last_target_language_fetch = 0

        self.usage = None
        self.last_usage_fetch = 0

    def get_last_source_languages(self):
        if 'last_source_languages' not in self.data:
            self.data['last_source_languages'] = []
        return self.data['last_source_languages']

    def get_last_target_languages(self):
        if 'last_target_languages' not in self.data:
            self.data['last_target_languages'] = []
        return self.data['last_target_languages']

    def set_last_source_language(self, lang):
        languages = self.get_last_source_languages()
        if lang in languages:
            languages.remove(lang)
        languages.insert(0, lang)
        json.dump(self.data, self.data_file.open('w'))

    def set_last_target_language(self, lang):
        languages = self.get_last_target_languages()
        if lang in languages:
            languages.remove(lang)
        languages.insert(0, lang)
        json.dump(self.data, self.data_file.open('w'))

    def get_source_languages(self):
        current = time.time()
        if current - self.last_source_language_fetch >= 600:
            self.source_languages = self.translator.get_source_languages()
            self.last_source_language_fetch = current
        return self.source_languages

    def get_target_languages(self):
        current = time.time()
        if current - self.last_target_language_fetch >= 600:
            self.target_languages = self.translator.get_target_languages()
            self.last_target_language_fetch = current
        return self.target_languages

    def get_source_language_name(self, lang_code):
        for language in self.get_source_languages():
            if language.code == lang_code:
                return language.name
        return None

    def get_target_language_name(self, lang_code):
        for language in self.get_target_languages():
            if language.code == lang_code:
                return language.name
        return None

    def get_usage(self):
        current = time.time()
        if current - self.last_usage_fetch >= 10:
            self.usage = self.translator.get_usage()
            self.last_usage_fetch = current
        return self.usage

    def on_input(self, keyword, arg):
        if not self.translator:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='Translator could not be initialized',
                                    description='Please validate that your API key is correct.',
                                    highlightable=False,
                                    on_enter=HideWindowAction())
            ])

        try:
            usage = self.get_usage().character
        except DeepLException as error:
            LOGGER.error(error)
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='An error occured',
                                    description='Please validate that your API key is correct.',
                                    highlightable=False,
                                    on_enter=HideWindowAction())
            ])

        if usage.limit_exceeded:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='DeepL API Usage exceeded',
                                    highlightable=False,
                                    on_enter=HideWindowAction())
            ])

        usage_str = f'Usage: {usage.count}/{usage.limit} ({round(usage.count / usage.limit * 10000) / 100}%)'
        if not arg:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='Enter text...',
                                    description=usage_str,
                                    highlightable=False,
                                    on_enter=DoNothingAction())
            ])

        items = [
            ExtensionResultItem(icon='images/icon.png',
                                name='Translate text',
                                description='Alt+Enter to skip input language and detect it instead.',
                                highlightable=False,
                                on_enter=ExtensionCustomAction({'keyword': keyword,
                                                                'text': arg}, keep_app_open=True),
                                on_alt_enter=ExtensionCustomAction({'keyword': keyword,
                                                                    'text': arg,
                                                                    'source_lang': None}, keep_app_open=True))
        ]

        last_target_languages = self.get_last_target_languages()
        for i in range(min(len(last_target_languages), 3)):
            lang = last_target_languages[i]
            items.append(ExtensionResultItem(icon='images/icon.png',
                                             name=f'Translate to {self.get_target_language_name(lang)}',
                                             description='Alt+Enter to choose input language.',
                                             highlightable=False,
                                             on_enter=ExtensionCustomAction({'keyword': keyword,
                                                                             'text': arg,
                                                                             'source_lang': None,
                                                                             'target_lang': lang}, keep_app_open=True),
                                             on_alt_enter=ExtensionCustomAction({'keyword': keyword,
                                                                                 'text': arg,
                                                                                 'target_lang': lang},
                                                                                keep_app_open=True)))

        return RenderResultListAction(items)


class SystemExitEventListener(EventListener):

    def on_event(self, event: SystemExitEvent, extension: DeepLExtension):
        json.dump(extension.data, extension.data_file.open('w'))


class PreferencesEventListener(EventListener):

    def on_event(self, event: PreferencesEvent, extension: DeepLExtension):
        api_key = event.preferences['api_key']
        extension.translator = Translator(api_key) if api_key else None


class PreferencesUpdateEventListener(EventListener):

    def on_event(self, event: PreferencesUpdateEvent, extension: DeepLExtension):
        if event.id == 'api_key':
            extension.translator = Translator(event.new_value) if event.new_value else None


class KeywordQueryEventListener(EventListener):

    def on_event(self, event: KeywordQueryEvent, extension: DeepLExtension):
        return extension.on_input(event.get_keyword(), event.get_argument())


class ItemEnterListener(EventListener):

    def on_event(self, event: ItemEnterEvent, extension: DeepLExtension):
        data = event.get_data()
        if 'reset' in data:
            return extension.on_input(data['keyword'], data['reset'])

        def compare(last_languages, lang1, lang2):
            l1, l2 = lang1.code, lang2.code
            e1, e2 = l1 in last_languages, l2 in last_languages
            if not e1 and not e2:
                return 0
            if e1 and not e2:
                return -1
            if not e1 and e2:
                return 1
            return last_languages.index(l1) - last_languages.index(l2)

        last_source_languages = extension.get_last_source_languages()
        last_target_languages = extension.get_last_target_languages()
        if 'source_lang' not in data:
            last_target = last_target_languages[0] if last_target_languages else None
            last_target_name = extension.get_target_language_name(last_target) if last_target else None

            languages = sorted(extension.get_source_languages(),
                               key=cmp_to_key(lambda lang1, lang2: compare(last_source_languages, lang1, lang2)))
            description = f'Alt+Enter to translate to {last_target_name}.' if last_target else ''

            detect_data = data.copy()
            detect_data['source_lang'] = None
            detect_alt_data = detect_data.copy()
            if last_target:
                detect_alt_data['target_lang'] = last_target
            items = [
                ExtensionResultItem(icon='images/icon.png',
                                    name='Detect language',
                                    description=description,
                                    highlightable=False,
                                    on_enter=ExtensionCustomAction(detect_data, keep_app_open=True),
                                    on_alt_enter=ExtensionCustomAction(detect_alt_data, keep_app_open=True))
            ]

            for language in languages:
                new_data = data.copy()
                new_data['source_lang'] = language.code
                new_alt_data = new_data.copy()
                if last_target:
                    new_alt_data['target_lang'] = last_target
                items.append(ExtensionResultItem(icon='images/icon.png',
                                                 name=f'Translate from {language.name}',
                                                 description=description,
                                                 highlightable=False,
                                                 on_enter=ExtensionCustomAction(new_data, keep_app_open=True),
                                                 on_alt_enter=ExtensionCustomAction(new_alt_data, keep_app_open=True)))

            return RenderResultListAction(items)
        elif data['source_lang']:
            extension.set_last_source_language(data['source_lang'])

        if 'target_lang' not in data:
            languages = sorted(extension.get_target_languages(),
                               key=cmp_to_key(lambda lang1, lang2: compare(last_target_languages, lang1, lang2)))

            items = []
            for language in languages:
                new_data = data.copy()
                new_data['target_lang'] = language.code
                items.append(ExtensionResultItem(icon='images/icon.png',
                                                 name=f'Translate to {language.name}',
                                                 highlightable=False,
                                                 on_enter=ExtensionCustomAction(new_data, keep_app_open=True)))

            return RenderResultListAction(items)
        if data['target_lang']:
            extension.set_last_target_language(data['target_lang'])

        try:
            supports_formality = False
            for language in extension.get_target_languages():
                if language.code == data['target_lang']:
                    supports_formality = language.supports_formality
            if supports_formality:
                try:
                    formality = Formality[extension.preferences['formality'].upper()]
                except KeyError:
                    formality = Formality.DEFAULT
            else:
                formality = Formality.DEFAULT

            result = extension.translator.translate_text(data['text'].strip(),
                                                         source_lang=data['source_lang'],
                                                         target_lang=data['target_lang'],
                                                         formality=formality)
            source_lang, target_lang = data['source_lang'] or result.detected_source_lang, data['target_lang']

            split_result = extension.preferences['split_result']
            shown_text = None
            if split_result.isnumeric():
                split_result_int = int(split_result)
                if split_result_int is not 0:
                    parts, current = [], None
                    for word in result.text.split(' '):
                        new_current = f'{current} {word}' if current else word
                        if not current or len(new_current) <= split_result_int:
                            current = new_current
                        else:
                            parts.append(current)
                            current = word
                    parts.append(current)
                    shown_text = '\n'.join(parts)
            if not shown_text:
                shown_text = result.text

            keyword = data['keyword']
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name=f'Translation: {extension.get_source_language_name(source_lang)} \u27A1 '
                                         f'{extension.get_target_language_name(target_lang)}',
                                    description=shown_text,
                                    highlightable=False,
                                    on_enter=CopyToClipboardAction(result.text),
                                    on_alt_enter=ExtensionCustomAction({'reset': result.text,
                                                                        'keyword': keyword}, keep_app_open=True)
                                    if data['text'] == result.text else SetUserQueryAction(f'{keyword} {result.text}')),
                ExtensionResultItem(icon='images/icon.png',
                                    name='Actions',
                                    description='Enter on the result item to copy the result.'
                                                '\nAlt+Enter on the result item to translate the result into another '
                                                'language.'
                                                '\nEnter on this item to translate again and reset the input text.'
                                                '\nAlt+Enter on this item to translate again and keep the input text.',
                                    highlightable=False,
                                    on_enter=SetUserQueryAction(f'{keyword} '),
                                    on_alt_enter=ExtensionCustomAction({'reset': data['text'],
                                                                        'keyword': keyword},
                                                                       keep_app_open=True))
            ])
        except DeepLException as error:
            LOGGER.error(error)
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='An error occured',
                                    highlightable=False,
                                    on_enter=HideWindowAction())
            ])


if __name__ == '__main__':
    DeepLExtension().run()
