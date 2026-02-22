GOAL:
* We want to create a desktop app which can be used to simulate daily situations where the user can chat with a bot in the target language. 
* We want to enable language practice in natural settings instead of getting stuck on grammar rules or vocabulary that may not be useful in practical scenarios.

FUNCTIONAL REQUIREMENTS:
* The app should be runnable locally
* The app should not require any expensive hardware 
* The app should be primarily developed in Python and served via a local webserver, running in the browser
* The app should leverage Ollama, using Gemma 3 (at least the 4B model) and require the user to install these if they are not available.
* The prompts that will be used with the model should be saved in separate files for ease of explainability and manual editability. These prompts are not expected to be edited by the app.
* While the model is thinking, the user should be notified so that they don't think the system is frozen
* There should be a settings menu which contains: 
** Dark Mode / Light Mode / System Default, 
** Model to use (populated from the list of locally available Gemma 3 4B/12B/27B Ollama models)
** Language to use for practice (populated from the list of available languages in Gemma 3, defaulted to Japanese)
** Language to use for the UI (one of English, Spanish, Chinese, Japanese, and Turkish)
** About (information on the project, its original author, and the licence)
* The list of situations to use for practice is to be dynamically generated using the model.
** When the app launches, run the model using a simple prompt to generate five different daily scenarios that can happen like buying a train ticket
** For each scenario create a clear setting and a goal
** There should be generated design elements, including clipart to go with the situation to keep it more interesting.
** Once the user chooses the scenario and understands the goal, the conversation should continue with a back and forth until that goal is reached.
** Some example goals would be: "The user manages to buy the ticket they need." or "The user manages to buy the snack they were looking for."
** Once the scenario is completed, the conversation should be saved locally on disk and a new scenario should be generated in its place in the list.
** The user should have a "HINT" button that would give a suggestion of what to ask next and how, and explain why that would make sense.
* If the practice language is Japanese the model should use proper Kanji but provide the reading in furigana so if the kanji is unfamiliar the user gets the reading.
* Each word in the practice language should be clickable to show a popup with the list of meanings/uses in the UI language.
* There should be a running score of how many situations the user has cleared so far. This should be clickable and should take the user to a list where they can click on each finished conversation and see how it happened.
* The user should have the option to abandon a conversation in the middle if they desire to do so. In such a case we won't save the conversation or remove it from the list of situations.

NON-FUNCTIONAL REQUIREMENTS:
* The user should not need to wait for longer than a few seconds to get a response
 
