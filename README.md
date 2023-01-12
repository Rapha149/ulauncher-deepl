# DeepL for Ulauncher
A powerful DeepL translator for Ulauncher.

## Features
- Translate text (kinda obvious)
- Quickly translate to the last used languages
- Use `from:to` in front of the text to choose languages even quicker! (See [Quick Language Selection](#quick-language-selection))
- Many options to customize the translator! (See [Preferences](#preferences))
- Copy the result to clipboard, translate it into another language or use the same input text again by pressing one button!
- Up to 500000 characters per month for free! (DeepL limitations)

![image](https://user-images.githubusercontent.com/49787110/204258768-28172c1f-0b50-442f-a742-1edb3c73aa7f.png)
![image](https://user-images.githubusercontent.com/49787110/204258777-8973375b-2a83-4057-8b77-33dae5792c85.png)
![image](https://user-images.githubusercontent.com/49787110/204258791-9f51eb3f-6643-40fe-8ff2-3b557e04d9bb.png)
![image](https://user-images.githubusercontent.com/49787110/212107654-d1bcd64b-215e-49bc-b636-e64d54b6fbeb.png)

## Requirements
`pip install deepl`

## Get an API key
You can get an DeepL API key for free at https://www.deepl.com/pro-api  
With free API keys you can translate up to 500000 characters per month.  
Of course you can also buy an API key and get more characters if needed.

## Quick Language Selection
Using the pattern `from:to` in front of the to be translated text you can quickly select the languages.  
For example: `en:es` to translate from English to Spanish.

You can also specify `auto` and `select` for the source language and `select` for the target language.  
If using `auto` the translator will automatically detect the source language.  
If using `select` you will be able to select the source/target language respectively.  
This is useful when you have selected languages in the preferences. Using this method you can temporarily "set" these settings to `auto` or `select`.

If you don't know a language code you can specify anything. The extension will tell you it doesn't know that language code and offer you a list of codes.

## Preferences
**Keyword**  
The keyword to use the extension.  
Defaults to `tr`.

**API key**  
Your DeepL API key. See [Get an API key](#get-an-api-key).

**Source language**  
The language you want to translate from.  
Set to `auto` to let DeepL detect the language automatically.  
Set to `select` to select the language manually each time.  
Set to a language code to always use that language. If you don't know the language code enter something else.
Then the extension will tell you that it doesn't know that language code and offer you a list of codes.  
Defaults to `select`.

**Target language**  
The language you want to translate to.  
Set to `select` to select the language manually each time.  
Set to a language code to always use that language. If you don't know the language code enter something else.
Then the extension will tell you that it doesn't know that language code and offer you a list of codes.  
Defaults to `select`.

**Number of quick access languages**  
Specifies how many languages to translate to are displayed for quick access.  
This setting applies only when `Target language` is set to `select`.  
Defaults to `3`.

**Number of languages per page**  
Specifies how many languages are displayed per page.  
Defaults to `10`.

**Split result in lines every `n` characters**  
Specifies after how many characters the result text is split into multiple lines.  
Words won't be split.  
Set to `0` to disable splitting. Warning: Large translated texts won't be displayed in full.   
Defaults to `65`.

**Formality of translated text**  
Specifies the formality of the translated text if available for the target language.  
Available options: `default`, `less` and `more`.  
Defaults to `default`.
