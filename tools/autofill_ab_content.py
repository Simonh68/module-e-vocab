#!/usr/bin/env python3
"""Create a first-pass A/B content file from curated rules and simple glosses.

The output is intentionally reviewed by the validation scripts before it is
used. It never changes the official entry/POS/family mapping.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import rebuild_official_vocab as vocab


DATAMUSE = Path("/tmp/module-e-datamuse")
HEBREW_GLOSSES = Path(__file__).resolve().parents[1] / "data/hebrew-glosses.json"

PHRASES = {
    # List A
    "among other things": ("including other things", "including some other things", "The center offers, among other things, free English lessons."),
    "at least": ("not less than", "not less than a number or amount", "At least ten students joined the activity."),
    "be responsible for": ("have the duty to care for", "have the duty to do or care for something", "Maya is responsible for organizing the class trip."),
    "come after/first/last": ("be later, first or last", "be in a later, first or last position", "The short questions come after the reading text."),
    "even if": ("whether or not", "whether or not something happens", "I will walk to school even if it rains."),
    "even though": ("although", "although something is true", "Even though Amir was tired, he finished his homework."),
    "except that": ("but with one difference", "but with one difference", "The two rooms are the same, except that this one has a balcony."),
    "focus on/upon": ("give attention to", "give special attention to someone or something", "Please focus on the main idea of the paragraph."),
    "in terms of": ("when considering", "when considering a particular part of something", "The plan is good in terms of cost."),
    "in actual fact": ("really", "used to show what is really true", "It looked easy, but in actual fact it was difficult."),
    "in connection with": ("related to", "related to a person, event or subject", "Police questioned him in connection with the accident."),
    "in that case": ("if that is true", "used to say what should happen if that is true", "In that case, we should leave earlier."),
    "in the meantime": ("during the time before", "during the time before something else happens", "Dinner will be ready soon; in the meantime, set the table."),
    "just about": ("almost", "almost, but not completely", "We have just about enough food for everyone."),
    "keep on doing": ("continue doing", "continue to do the same action", "She kept on working after everyone else had left."),
    "kind of": ("a little; in some way", "a little or in some way", "This puzzle is kind of difficult."),
    "look at": ("direct your eyes or attention to", "direct your eyes or attention toward something", "Let's look at the results together."),
    "more or less": ("almost; about", "almost or approximately", "The work is more or less complete."),
    "not at all": ("in no way", "in no way or by no amount", "I am not at all worried about the test."),
    "not only": ("as well as", "used to add another important fact", "She is not only clever but also very kind."),
    "on the one hand ... on the other hand": ("two different sides", "used to compare two different sides of a situation", "On the one hand the job pays well; on the other hand it is far away."),
    "out of date": ("old and no longer useful", "too old to be useful or correct", "This map is out of date."),
    "point of view": ("opinion; way of seeing", "a way of thinking about or seeing something", "From my point of view, the rule is fair."),
    "provided that": ("only if", "only if a particular condition is met", "You can borrow the bike provided that you return it today."),
    "rely on/upon": ("depend on; trust", "depend on or trust someone or something", "You can rely on Dana to keep her promise."),
    "run out of": ("have none left", "use all of something so that none remains", "We ran out of milk this morning."),
    "set up": ("start; arrange", "start or arrange something for use", "The students set up a new reading club."),
    "take advantage of": ("use a good chance", "use an opportunity in a helpful way", "We took advantage of the sunny day and went outside."),
    "thanks to": ("because of", "because of someone or something helpful", "Thanks to your help, we finished on time."),
    "throw away/out": ("put in the trash", "get rid of something that is not wanted", "Do not throw away the empty bottle; recycle it."),
    # List B
    "all of a sudden": ("suddenly", "very suddenly and without warning", "All of a sudden, the lights went out."),
    "be in charge": ("be responsible", "have control or responsibility for something", "Rina is in charge of the school library."),
    "be situated in/on/by": ("be located", "be in a particular place", "The hotel is situated by the sea."),
    "believe in": ("think is good, true or real", "think that someone or something is good, true or real", "I believe in giving everyone a fair chance."),
    "bring up": ("mention; raise", "mention a subject or raise a child", "She brought up an important question during the meeting."),
    "cut down": ("reduce; make fall", "reduce an amount or make a tree fall", "We should cut down the amount of plastic we use."),
    "either way": ("in both cases", "used when the result is the same in both cases", "We can walk or take the bus; either way, we will arrive on time."),
    "fed up": ("tired and annoyed", "tired and annoyed because something continued too long", "He was fed up with waiting."),
    "get rid of": ("remove; throw away", "remove something that is not wanted", "We need to get rid of these broken chairs."),
    "get wrong": ("make a mistake about", "understand or answer something incorrectly", "I got the last question wrong."),
    "get worse": ("become more bad", "become more difficult, painful or serious", "Her cold began to get worse at night."),
    "give away": ("give for free; reveal", "give something for free or reveal a secret", "They gave away warm clothes to families in need."),
    "go out": ("leave home; stop burning", "leave home for an activity or stop giving light", "We went out for dinner on Friday."),
    "it looks like/as if/as though": ("it seems", "used to say how a situation seems", "It looks as if the rain will stop soon."),
    "just as ... as": ("equally", "equal to someone or something in a particular way", "The second exercise is just as difficult as the first."),
    "look forward to": ("feel happy about the future", "feel pleased and excited about something in the future", "I look forward to seeing you next week."),
    "make sense": ("be clear and reasonable", "be easy to understand or reasonable", "Your explanation makes sense."),
    "make up": ("invent; form", "invent something or form part of a whole", "The children made up a funny story."),
    "make up your mind": ("decide", "make a decision after thinking", "Please make up your mind before Friday."),
    "neither ... nor": ("not one and not the other", "not the first choice and not the second choice", "Neither Tom nor Maya was late."),
    "not ... a word": ("nothing at all", "used to say that nothing was heard, said or understood", "I did not understand a word of the speech."),
    "not until": ("only after a time", "only after a particular time or event", "We did not leave until the rain stopped."),
    "on the whole": ("generally", "when considering everything together", "On the whole, the trip was successful."),
    "part-time": ("for only part of the week", "for fewer hours than a full working week", "She has a part-time job at a café."),
    "put up with": ("accept something annoying", "accept an unpleasant situation without complaining", "I cannot put up with this noise any longer."),
    "shut down": ("close; stop operating", "close a place or stop a machine from working", "The factory shut down for repairs."),
    "slow down/up": ("move less or more quickly", "make someone or something move less or more quickly", "Please slow down near the school."),
    "so-called": ("called by that name", "used for a name that may not be correct", "The so-called expert could not answer the question."),
    "sooner or later": ("at some future time", "at some time in the future, even if the time is unknown", "Sooner or later, we will need to replace the old computer."),
    "start off": ("begin", "begin an activity or journey in a particular way", "The lesson started off with a short game."),
    "sum up": ("give the main points", "state the main ideas in a short form", "Please sum up the article in two sentences."),
    "take into account": ("consider", "consider a fact when making a decision", "We must take the weather into account."),
    "take part": ("join an activity", "join and be involved in an activity", "Every student can take part in the competition."),
    "take place": ("happen", "happen at a particular time or place", "The ceremony will take place on Monday."),
    "take the opportunity": ("use a good chance", "use a suitable chance to do something", "I took the opportunity to thank my teacher."),
    "take seriously": ("treat as important", "treat someone or something as important and real", "You should take this warning seriously."),
    "take/accept/claim responsibility": ("say you are responsible", "accept that you have a duty or caused something", "The manager accepted responsibility for the mistake."),
    "the headlines": ("main news titles", "the titles of the most important news stories", "The election result was in the headlines."),
    "the heart of": ("the center; most important part", "the central or most important part of something", "Trust is at the heart of a good friendship."),
    "the main thing": ("the most important point", "the most important fact, idea or goal", "The main thing is that everyone is safe."),
    "the reality of": ("the true situation", "the situation as it really is", "The report describes the reality of life in the city."),
    "to start with": ("at first; first", "used to introduce the first point or situation", "To start with, read the title carefully."),
    "up-to-date": ("modern and current", "containing the newest information", "The website gives up-to-date travel information."),
    "use up": ("use all of", "use all of something so that none remains", "We used up all the paper."),
    "virtual reality": ("computer-made world", "a computer-made world that seems real", "Students explored the museum through virtual reality."),
}

FUNCTION_WORDS = {
    ("as", "Conjunction"): ("while; because; in the same way", "used to connect two events, reasons or comparisons", "As I was leaving, the phone rang."),
    ("before", "Preposition"): ("earlier than", "earlier than a time or event", "Please finish the work before lunch."),
    ("besides", "Adverb"): ("also; in addition", "used to add another reason or fact", "I am tired; besides, it is already late."),
    ("besides", "Preposition"): ("apart from; in addition to", "apart from or in addition to someone or something", "Besides English, she speaks Hebrew."),
    ("can", "Verb"): ("be able to; sometimes happen", "be able to do something or show that something is possible", "Cold weather can make the roads dangerous."),
    ("do", "Auxiliary verb"): ("used for emphasis", "used before another verb to make a statement stronger", "I do understand your concern."),
    ("from", "Preposition"): ("starting at; coming out of", "used to show a starting place, time or source", "The train goes from Haifa to Tel Aviv."),
    ("in", "Preposition"): ("inside; during; showing a state", "inside a place, during a time or showing a particular state", "The children are in the garden."),
    ("must", "Verb"): ("have to; be very likely", "have to do something or show that something is very likely", "You must wear a seat belt."),
    ("once", "Conjunction"): ("as soon as", "as soon as something has happened", "Once you finish, check your answers."),
    ("others", "Pronoun"): ("other people or things", "other people or things that were not already named", "Some students agreed, but others did not."),
    ("otherwise", "Adverb"): ("if not; in another way", "used to show what happens if something is not done", "Leave now; otherwise, you will miss the bus."),
    ("otherwise", "Conjunction"): ("if not", "used to show a different result if something is not done", "Hurry, otherwise we will be late."),
    ("unlike", "Preposition"): ("different from", "different from another person or thing", "Unlike his brother, Dan enjoys cooking."),
    ("whom", "Pronoun"): ("which person", "used instead of 'who' as the object of a verb or preposition", "Whom did you invite to the meeting?"),
    ("within", "Adverb"): ("inside; not beyond", "inside a place or before a limit is reached", "The answer came from within."),
    ("within", "Preposition"): ("inside; before a limit", "inside a place, time or limit", "Please reply within three days."),
    ("would", "Verb"): ("past form of will; polite wish", "used for the past form of 'will' or to speak politely", "She said she would call later."),
    ("above", "Adjective"): ("written earlier", "written or mentioned earlier on the page", "Read the above instructions carefully."),
    ("behind", "Adverb"): ("later; slower; at the back", "at the back or making less progress than others", "After missing a week, he fell behind."),
    ("indoors", "Adjective"): ("inside a building", "happening or used inside a building", "They planned an indoors activity because of the rain."),
    ("indoors", "Adverb"): ("inside a building", "inside a building", "It was raining, so we stayed indoors."),
    ("to", "Preposition"): ("toward; until", "used for direction, a receiver or the end of a range", "The shop is open from nine to five."),
    ("underneath", "Adverb"): ("below", "in or to a lower position", "The box is heavy, but there is a handle underneath."),
    ("underneath", "Preposition"): ("below", "directly below someone or something", "The keys were underneath the book."),
    ("wherever", "Adverb"): ("in any place", "in or to any place", "Sit wherever you like."),
}

MULTI_POS_GLOSSES = {
    ("approach", "Verb"): "move closer; deal with",
    ("approach", "Noun"): "way or method",
    ("decrease", "Verb"): "become or make smaller",
    ("decrease", "Noun"): "reduction",
    ("dislike", "Verb"): "not like",
    ("dislike", "Noun"): "feeling of not liking",
    ("drop", "Verb"): "fall; let fall",
    ("drop", "Noun"): "small amount of liquid; fall",
    ("flood", "Verb"): "cover with water",
    ("flood", "Noun"): "too much water over dry land",
    ("gain", "Verb"): "get; increase",
    ("gain", "Noun"): "increase; benefit",
    ("interest", "Verb"): "make curious",
    ("interest", "Noun"): "curiosity; activity you enjoy",
    ("likely", "Adjective"): "probable",
    ("likely", "Adverb"): "probably",
    ("mention", "Verb"): "speak about briefly",
    ("mention", "Noun"): "short reference",
    ("protest", "Verb"): "show strong disagreement",
    ("protest", "Noun"): "public show of disagreement",
    ("regard", "Verb"): "consider; think of",
    ("regard", "Noun"): "respect; attention",
    ("request", "Verb"): "ask for",
    ("request", "Noun"): "polite demand",
    ("research", "Verb"): "study carefully to find facts",
    ("research", "Noun"): "careful study to find facts",
    ("review", "Verb"): "examine again; give an opinion",
    ("review", "Noun"): "examination; written opinion",
    ("risk", "Verb"): "do something that may cause harm",
    ("risk", "Noun"): "chance of harm",
    ("study", "Verb"): "learn; examine carefully",
    ("study", "Noun"): "learning; piece of research",
    ("transport", "Verb"): "carry from one place to another",
    ("transport", "Noun"): "system for moving people or things",
    ("double", "Verb"): "make twice as much",
    ("double", "Adverb"): "twice as much",
    ("export", "Verb"): "send goods to another country",
    ("export", "Noun"): "goods sent to another country",
    ("farther/further", "Adjective"): "more distant; additional",
    ("farther/further", "Adverb"): "at or to a greater distance",
    ("import", "Verb"): "bring goods into a country",
    ("import", "Noun"): "goods brought into a country",
    ("lecture", "Verb"): "give a formal talk",
    ("lecture", "Noun"): "formal educational talk",
    ("principal", "Adjective"): "main",
    ("principal", "Noun"): "head of a school",
    ("reach", "Verb"): "arrive at; stretch to touch",
    ("reach", "Noun"): "distance someone can touch",
    ("record", "Verb"): "store sound, pictures or information",
    ("record", "Noun"): "stored information; best result",
    ("register", "Verb"): "put a name on an official list",
    ("register", "Noun"): "official list",
    ("regret", "Verb"): "feel sorry about",
    ("regret", "Noun"): "feeling of sadness about the past",
    ("remark", "Verb"): "say; comment",
    ("remark", "Noun"): "comment",
    ("rescue", "Verb"): "save from danger",
    ("rescue", "Noun"): "act of saving from danger",
    ("respect", "Verb"): "admire; treat well",
    ("respect", "Noun"): "admiration; polite treatment",
    ("rule", "Verb"): "govern; control",
    ("rule", "Noun"): "official instruction",
    ("rush", "Verb"): "move or act very quickly",
    ("rush", "Noun"): "sudden quick movement; busy time",
    ("support", "Verb"): "help; agree with",
    ("support", "Noun"): "help; agreement",
    ("waste", "Verb"): "use badly or use too much",
    ("waste", "Adjective"): "not wanted and left over",
    ("welcome", "Verb"): "greet with pleasure",
    ("welcome", "Adjective"): "pleasing and wanted",
}

# Human-reviewed, POS-specific definitions and examples for the official
# single-word entries. The wording is deliberately short and learner-friendly.
CURATED = {
    # List A
    ("addition", "Noun"): ("an extra thing or part", "We made one small addition to the plan.", "extra part"),
    ("advance", "Noun"): ("movement forward; progress", "The team made an important advance in its research.", "progress"),
    ("advanced", "Adjective"): ("at a high or modern level", "She studies advanced English.", "high-level; modern"),
    ("advertising", "Noun"): ("messages that try to sell products", "Online advertising can reach many people.", "commercial messages"),
    ("analysis", "Noun"): ("careful study of parts or information", "The report includes an analysis of the results.", "careful study"),
    ("appear", "Verb"): ("come into view; seem", "A rainbow appeared after the rain.", "seem; come into view"),
    ("approach", "Noun"): ("a way of doing or thinking about something", "This teaching approach helps beginners.", "method; way"),
    ("approach", "Verb"): ("move closer; begin to deal with", "We approached the problem calmly.", "move closer; deal with"),
    ("average", "Adjective"): ("ordinary; not especially high or low", "Her score was close to the average result.", "ordinary; usual"),
    ("challenge", "Verb"): ("question or disagree with something", "The student challenged the speaker's claim.", "question; disagree with"),
    ("chance", "Noun"): ("an opportunity or a possibility", "Everyone deserves a fair chance to succeed.", "opportunity; possibility"),
    ("change", "Verb"): ("become different; make something different", "The weather can change quickly.", "become different"),
    ("characteristic", "Noun"): ("a usual or special quality", "Patience is an important characteristic of a good teacher.", "quality; feature"),
    ("claim", "Verb"): ("say that something is true", "The company claims that the product is safe.", "state; say is true"),
    ("common", "Adjective"): ("usual; shared by many", "This is a common mistake.", "usual; shared"),
    ("complicated", "Adjective"): ("difficult to understand or deal with", "The instructions seemed complicated at first.", "complex; difficult"),
    ("concern", "Verb"): ("worry someone; be about something", "The rising cost concerns many families.", "worry; be about"),
    ("conditions", "Noun"): ("the situation in which people or things exist", "The workers asked for safer conditions.", "circumstances"),
    ("conduct", "Verb"): ("organize and carry out", "The class conducted a short survey.", "carry out"),
    ("consequence", "Noun"): ("a result of an action or event", "One consequence of the storm was a power cut.", "result; effect"),
    ("considerable", "Adjective"): ("large or important", "The project required considerable effort.", "large; important"),
    ("cope", "Verb"): ("deal successfully with something difficult", "She learned to cope with the pressure.", "deal successfully"),
    ("critic", "Noun"): ("a person who judges or gives opinions", "The film critic wrote a positive review.", "reviewer"),
    ("current", "Adjective"): ("happening or existing now", "The article describes the current situation.", "present; now"),
    ("decrease", "Noun"): ("a reduction in size, number or amount", "There was a decrease in road accidents.", "reduction"),
    ("decrease", "Verb"): ("become or make smaller", "Prices may decrease next month.", "become smaller"),
    ("delayed", "Adjective"): ("happening later than planned", "The delayed train arrived at noon.", "late"),
    ("deliberately", "Adverb"): ("on purpose", "He deliberately left the answer blank.", "on purpose"),
    ("demonstrate", "Verb"): ("show clearly; protest in public", "The teacher demonstrated how to use the tool.", "show; protest"),
    ("design", "Noun"): ("a plan for how something will look or work", "The building has a simple design.", "plan; style"),
    ("destruction", "Noun"): ("very serious damage", "The fire caused the destruction of several homes.", "serious damage"),
    ("development", "Noun"): ("growth, change or a new event", "The new hospital is an important development.", "growth; change"),
    ("disagreement", "Noun"): ("a situation in which people have different opinions", "The two friends had a disagreement about money.", "difference of opinion"),
    ("disaster", "Noun"): ("an event that causes great harm", "The earthquake was a terrible disaster.", "catastrophe"),
    ("discovery", "Noun"): ("something found or learned for the first time", "The scientists announced an important discovery.", "new finding"),
    ("dislike", "Noun"): ("a feeling of not liking someone or something", "He has a strong dislike of loud music.", "feeling of not liking"),
    ("dislike", "Verb"): ("not like", "Many children dislike waking up early.", "not like"),
    ("doubt", "Verb"): ("feel unsure that something is true", "I doubt that the story is true.", "not be sure"),
    ("drop", "Noun"): ("a small amount of liquid; a fall", "A drop of rain fell on the page.", "small liquid amount; fall"),
    ("drop", "Verb"): ("fall; let something fall", "Be careful not to drop the glass.", "fall; let fall"),
    ("educate", "Verb"): ("teach and help someone learn", "Schools educate young people for the future.", "teach"),
    ("efficient", "Adjective"): ("working well without wasting time or energy", "The new system is simple and efficient.", "effective; not wasteful"),
    ("emphasis", "Noun"): ("special attention or importance", "The course places emphasis on speaking.", "special importance"),
    ("enjoyable", "Adjective"): ("pleasant and fun", "We had an enjoyable evening together.", "pleasant; fun"),
    ("essay", "Noun"): ("a short piece of writing about a subject", "She wrote an essay about city life.", "written composition"),
    ("essentially", "Adverb"): ("in the most important way; basically", "The two plans are essentially the same.", "basically"),
    ("event", "Noun"): ("something that happens; an organized activity", "The school event begins at six.", "happening; organized activity"),
    ("exactly", "Adverb"): ("completely correctly; in full agreement", "That is exactly what I meant.", "precisely"),
    ("exist", "Verb"): ("be real or present", "Some plants can exist with very little water.", "be real; be present"),
    ("extraordinary", "Adjective"): ("very unusual or special", "She showed extraordinary courage.", "unusual; special"),
    ("feature", "Noun"): ("an important or noticeable part", "The camera has a useful new feature.", "important part"),
    ("feedback", "Noun"): ("comments that help someone improve", "The teacher gave helpful feedback on my writing.", "helpful comments"),
    ("figure", "Noun"): ("a number, shape or picture", "The sales figure increased this year.", "number; shape; picture"),
    ("financial", "Adjective"): ("connected with money", "The family needed financial help.", "related to money"),
    ("finding/findings", "Noun"): ("a result learned from research", "The main finding surprised the researchers.", "research result"),
    ("flexible", "Adjective"): ("able to change easily when needed", "Our schedule is flexible.", "adaptable"),
    ("flood", "Noun"): ("water covering land that is usually dry", "The flood damaged many houses.", "overflowing water"),
    ("flood", "Verb"): ("cover a place with too much water", "Heavy rain flooded the road.", "cover with water"),
    ("flu", "Noun"): ("an illness like a bad cold", "She stayed home because she had the flu.", "influenza"),
    ("focus", "Noun"): ("the main point of attention", "Safety is the main focus of the meeting.", "center of attention"),
    ("frequent", "Adjective"): ("happening often", "Frequent practice improves your English.", "often happening"),
    ("fresh", "Adjective"): ("new, recent or not spoiled", "We bought fresh bread this morning.", "new; recent; not spoiled"),
    ("frighten", "Verb"): ("make someone feel afraid", "The sudden noise frightened the child.", "scare"),
    ("gain", "Noun"): ("an increase or benefit", "The change brought a small gain in speed.", "increase; benefit"),
    ("gain", "Verb"): ("get or increase", "Students gain confidence through practice.", "get; increase"),
    ("generate", "Verb"): ("produce or create", "Solar panels generate electricity.", "create; produce"),
    ("guidance", "Noun"): ("advice that helps someone decide what to do", "Students can ask the counselor for guidance.", "advice"),
    ("hopefully", "Adverb"): ("used to say that you hope something will happen", "Hopefully, the weather will improve tomorrow.", "with hope"),
    ("ideal", "Adjective"): ("perfect or most suitable", "This quiet room is ideal for studying.", "perfect; most suitable"),
    ("illness", "Noun"): ("a condition of being sick", "He missed school because of an illness.", "sickness"),
    ("illustrate", "Verb"): ("explain by using a picture or example", "The chart illustrates the change in temperature.", "show with example or picture"),
    ("image", "Noun"): ("a picture or the idea people have of something", "The screen displayed a clear image.", "picture; public impression"),
    ("initial", "Adjective"): ("first", "Our initial plan was too expensive.", "first"),
    ("instruction", "Noun"): ("information that tells someone what to do", "Read each instruction carefully.", "direction; teaching"),
    ("intelligence", "Noun"): ("the ability to learn and understand", "The test measures several kinds of intelligence.", "ability to understand"),
    ("interest", "Noun"): ("curiosity; an activity someone enjoys", "Her interest in science began at school.", "curiosity; hobby"),
    ("interest", "Verb"): ("make someone curious", "The story may interest young readers.", "make curious"),
    ("introduce", "Verb"): ("present someone or something for the first time", "The teacher introduced a new topic.", "present for first time"),
    ("invest", "Verb"): ("put in money, time or effort for a future benefit", "They invested money in a small business.", "put in for future benefit"),
    ("investigate", "Verb"): ("try to discover the facts", "Police are investigating the accident.", "examine; find facts"),
    ("knowledge", "Noun"): ("information and understanding", "Reading increases our knowledge of the world.", "understanding; information"),
    ("lack", "Verb"): ("not have enough of something", "The village lacks clean water.", "not have enough"),
    ("landscape", "Noun"): ("the visible features of an area of land", "The desert landscape was beautiful.", "view of the land"),
    ("likely", "Adjective"): ("probable", "Rain is likely this evening.", "probable"),
    ("likely", "Adverb"): ("probably", "The team will likely arrive late.", "probably"),
    ("limited", "Adjective"): ("small in amount or number", "Only a limited number of tickets remain.", "restricted; small"),
    ("little", "Adjective"): ("small in size or amount", "We had little time to prepare.", "small; not much"),
    ("low", "Adverb"): ("at a small height, amount or level", "The plane flew low over the field.", "at a small level"),
    ("material", "Noun"): ("information, documents or a substance used to make things", "The teacher uploaded the study material.", "information; substance"),
    ("mean", "Verb"): ("have a particular meaning or purpose", "What does this expression mean?", "signify"),
    ("means", "Noun"): ("a method or way", "Email is a useful means of communication.", "method; way"),
    ("measure", "Noun"): ("an action taken to achieve something", "The school introduced a safety measure.", "step; method"),
    ("mention", "Noun"): ("a short reference to someone or something", "The article made no mention of the cost.", "brief reference"),
    ("mention", "Verb"): ("speak or write about briefly", "Please mention the source in your answer.", "refer to briefly"),
    ("miss", "Verb"): ("fail to do, see or reach something", "Hurry or you will miss the bus.", "fail to reach or do"),
    ("misunderstand", "Verb"): ("understand incorrectly", "I misunderstood the last question.", "understand wrongly"),
    ("naturally", "Adverb"): ("as expected; in a normal way", "Naturally, her parents were worried.", "as expected; normally"),
    ("nature", "Noun"): ("the basic character or type of something", "We discussed the nature of the problem.", "character; type"),
    ("necessarily", "Adverb"): ("as a necessary result; always", "A high price does not necessarily mean good quality.", "unavoidably; always"),
    ("nevertheless", "Adverb"): ("despite what was just said", "The task was difficult; nevertheless, we completed it.", "however; even so"),
    ("notice", "Noun"): ("a written message or advance warning", "The school posted a notice about the trip.", "message; warning"),
    ("objective", "Noun"): ("an aim or purpose", "Our main objective is to improve reading skills.", "goal; aim"),
    ("occasional", "Adjective"): ("happening sometimes but not often", "We have occasional meetings after school.", "not frequent"),
    ("official", "Adjective"): ("approved by a person or organization in authority", "Check the official website for details.", "authorized"),
    ("participate", "Verb"): ("take part", "All students may participate in the discussion.", "take part"),
    ("particular", "Adjective"): ("specific; special", "I am looking for a particular book.", "specific"),
    ("past", "Adjective"): ("belonging to an earlier time", "Past experience can help us decide.", "previous"),
    ("perform", "Verb"): ("do an action or entertain an audience", "The band will perform tonight.", "carry out; entertain"),
    ("personality", "Noun"): ("the qualities that make a person behave in a certain way", "She has a friendly personality.", "character"),
    ("personally", "Adverb"): ("in your own opinion; by yourself", "Personally, I prefer the first plan.", "in my own opinion"),
    ("planet", "Noun"): ("a large round object moving around a star", "Earth is the third planet from the sun.", "world orbiting a star"),
    ("planning", "Noun"): ("the activity of deciding how to do something", "Careful planning made the event successful.", "preparation"),
    ("plant", "Verb"): ("put a seed or young tree in the ground", "We planted a tree in the school yard.", "put in the ground"),
    ("policy", "Noun"): ("an official plan or rule", "The school has a clear phone policy.", "official plan; rule"),
    ("pollution", "Noun"): ("harmful material in air, water or land", "Traffic causes air pollution.", "environmental contamination"),
    ("popular", "Adjective"): ("liked by many people; common", "This game is popular with teenagers.", "well-liked; widespread"),
    ("population", "Noun"): ("all the people living in an area", "The city's population is growing.", "people in an area"),
    ("prevent", "Verb"): ("stop something from happening", "Seat belts help prevent injuries.", "stop"),
    ("priority", "Noun"): ("something more important than other things", "Student safety is our first priority.", "main concern"),
    ("private", "Adjective"): ("not public; belonging to one person or company", "This is a private conversation.", "personal; not public"),
    ("probable", "Adjective"): ("likely to be true or happen", "The probable cause was a broken wire.", "likely"),
    ("produce", "Verb"): ("make or create", "The factory produces medical equipment.", "make; create"),
    ("profession", "Noun"): ("a job that needs special training", "Teaching is a demanding profession.", "trained occupation"),
    ("professor", "Noun"): ("a senior teacher at a university", "The professor answered the student's question.", "university teacher"),
    ("proof", "Noun"): ("information showing that something is true", "The photo provided proof of the damage.", "evidence"),
    ("proposed", "Adjective"): ("suggested for people to consider", "The proposed change will be discussed tomorrow.", "suggested"),
    ("protest", "Noun"): ("a public show of strong disagreement", "Hundreds joined the peaceful protest.", "public objection"),
    ("protest", "Verb"): ("show strong disagreement", "Residents protested against the plan.", "object publicly"),
    ("psychology", "Noun"): ("the study of the mind and behavior", "She plans to study psychology.", "study of mind and behavior"),
    ("public", "Adjective"): ("open to everyone; connected with government", "The city opened a new public park.", "open to all; governmental"),
    ("purpose", "Noun"): ("the reason for doing something", "The purpose of the meeting is to share information.", "aim; reason"),
    ("quality", "Noun"): ("how good something is; a feature", "The product is known for its high quality.", "standard; feature"),
    ("question", "Noun"): ("something asked; a problem to discuss", "The final question was difficult.", "inquiry; issue"),
    ("question", "Verb"): ("ask someone for information; doubt", "Police questioned the driver.", "ask; doubt"),
    ("questionnaire", "Noun"): ("a written set of questions", "Students completed a short questionnaire.", "survey form"),
    ("react", "Verb"): ("respond to something", "How did she react to the news?", "respond"),
    ("reasonable", "Adjective"): ("fair, sensible or not too expensive", "The shop offered a reasonable price.", "fair; sensible"),
    ("recommend", "Verb"): ("say that something is good or suitable", "I recommend this book to beginners.", "suggest"),
    ("recycle", "Verb"): ("process used material so it can be used again", "Please recycle the empty bottles.", "use again"),
    ("regard", "Noun"): ("respect or attention", "She has great regard for her teacher.", "respect"),
    ("regard", "Verb"): ("consider or think of in a certain way", "Many people regard exercise as important.", "consider"),
    ("region", "Noun"): ("a large area of a country or the world", "The northern region receives more rain.", "area"),
    ("regular", "Adjective"): ("normal; happening at fixed times", "Regular exercise is good for your health.", "normal; repeated"),
    ("relevant", "Adjective"): ("connected with the subject", "Include only relevant information.", "related"),
    ("reliable", "Adjective"): ("able to be trusted or depended on", "We need a reliable source of information.", "dependable"),
    ("request", "Noun"): ("a polite or official ask for something", "The manager accepted our request.", "formal ask"),
    ("request", "Verb"): ("ask for something politely or officially", "You may request extra time.", "ask for"),
    ("research", "Noun"): ("careful study to discover facts", "The project is based on scientific research.", "careful study"),
    ("research", "Verb"): ("study carefully to discover facts", "Students researched the history of the town.", "investigate"),
    ("result", "Noun"): ("what happens because of an action or event", "The result of the test was encouraging.", "outcome"),
    ("review", "Noun"): ("an examination or written opinion", "I read a positive review of the film.", "assessment; opinion"),
    ("review", "Verb"): ("examine again; give an opinion", "Please review your answers before submitting.", "check again"),
    ("revise", "Verb"): ("study again or make changes", "I need to revise for tomorrow's test.", "review; change"),
    ("risk", "Noun"): ("a chance that something harmful may happen", "Driving too fast is a serious risk.", "danger; chance of harm"),
    ("risk", "Verb"): ("do something that may cause harm or loss", "Do not risk your safety.", "take a chance"),
    ("rural", "Adjective"): ("connected with the countryside", "They live in a rural area.", "countryside"),
    ("salary", "Noun"): ("money paid regularly for work", "Her monthly salary increased.", "regular pay"),
    ("sample", "Noun"): ("a small part used to represent the whole", "The doctor tested a blood sample.", "representative part"),
    ("seldom", "Adverb"): ("not often", "We seldom watch television during dinner.", "rarely"),
    ("sense", "Noun"): ("good judgment; a feeling or meaning", "It makes sense to check the weather first.", "judgment; feeling"),
    ("significant", "Adjective"): ("important or large enough to notice", "There was a significant improvement in her score.", "important; noticeable"),
    ("skilled", "Adjective"): ("having training and ability", "A skilled worker repaired the machine.", "trained; able"),
    ("slight", "Adjective"): ("small and not serious", "There was a slight delay.", "small; minor"),
    ("specialist", "Noun"): ("a person with expert knowledge in one area", "The doctor sent her to a heart specialist.", "expert"),
    ("specific", "Adjective"): ("clear and exact; particular", "Please give a specific example.", "exact; particular"),
    ("still", "Adverb"): ("continuing until now; even so", "It was late, but she was still working.", "yet; continuing"),
    ("structure", "Noun"): ("the way parts are arranged", "The essay has a clear structure.", "organization of parts"),
    ("study", "Noun"): ("learning or a piece of research", "The study found that sleep improves memory.", "research; learning"),
    ("study", "Verb"): ("learn about or examine carefully", "She studies English every evening.", "learn; examine"),
    ("supposed", "Adjective"): ("believed or expected to be true", "The supposed expert gave poor advice.", "believed; expected"),
    ("surface", "Noun"): ("the outside or top layer", "The table has a smooth surface.", "outer layer"),
    ("theory", "Noun"): ("an idea that explains how or why something happens", "The evidence supports the theory.", "explanatory idea"),
    ("transport", "Noun"): ("a system for moving people or goods", "Public transport is cheaper than driving.", "transportation system"),
    ("transport", "Verb"): ("carry people or goods to another place", "Trucks transport food across the country.", "carry"),
    ("trash", "Noun"): ("things that are thrown away", "Put the trash in the bin.", "rubbish"),
    ("treatment", "Noun"): ("medical care; the way someone is dealt with", "The patient received immediate treatment.", "medical care; handling"),
    ("unfortunately", "Adverb"): ("used to say that something is sad or disappointing", "Unfortunately, the event was canceled.", "sadly"),
    ("unhealthy", "Adjective"): ("not good for the body or mind", "Too much sugar is unhealthy.", "not healthy"),
    ("unique", "Adjective"): ("the only one of its kind; very unusual", "Each person has a unique voice.", "one of a kind"),
    ("united", "Adjective"): ("joined together for the same purpose", "The community remained united.", "joined together"),
    ("universe", "Noun"): ("all space, matter and energy", "Scientists study the age of the universe.", "all of space"),
    ("unknown", "Adjective"): ("not known", "The cause of the problem is unknown.", "not known"),
    ("unlikely", "Adjective"): ("not expected to happen or be true", "Rain is unlikely today.", "not probable"),
    ("urban", "Adjective"): ("connected with a city", "The project studies urban life.", "city-related"),
    ("vary", "Verb"): ("be different or change", "Prices vary from shop to shop.", "differ; change"),
    ("view", "Noun"): ("an opinion; what can be seen", "The room has a beautiful view of the sea.", "opinion; sight"),
    ("visible", "Adjective"): ("able to be seen", "The mountains were clearly visible.", "can be seen"),
    ("vision", "Noun"): ("the ability to see; an idea for the future", "The leader shared her vision for the school.", "sight; future idea"),
    ("volume", "Noun"): ("amount; level of sound; one book in a series", "Please turn down the volume.", "amount; sound level"),
    ("wildlife", "Noun"): ("animals and plants living in nature", "The park protects local wildlife.", "wild animals and plants"),
    ("worthwhile", "Adjective"): ("valuable enough to be worth the time or effort", "The course was difficult but worthwhile.", "valuable; useful"),
}

CURATED.update({
    # List B
    ("account", "Noun"): ("a written or spoken report; a bank arrangement", "The witness gave a clear account of what happened.", "report; bank arrangement"),
    ("acquire", "Verb"): ("get or learn something", "Students acquire new skills through practice.", "get; learn"),
    ("age", "Noun"): ("the number of years someone has lived", "Children can join the course at the age of twelve.", "years lived"),
    ("agriculture", "Noun"): ("the work of growing crops and raising animals", "Agriculture is important to the local economy.", "farming"),
    ("altogether", "Adverb"): ("completely; in total", "There were twenty students altogether.", "completely; in total"),
    ("anxious", "Adjective"): ("worried or nervous", "She felt anxious before the interview.", "worried; nervous"),
    ("apparent", "Adjective"): ("easy to notice or understand", "It became apparent that we needed more time.", "clear; noticeable"),
    ("appropriate", "Adjective"): ("right or suitable for a situation", "Wear appropriate shoes for the long walk.", "suitable"),
    ("atmosphere", "Noun"): ("the air around a planet; the feeling in a place", "The café has a warm and friendly atmosphere.", "air around a planet; feeling"),
    ("automatically", "Adverb"): ("by itself, without a person controlling it", "The lights turn off automatically.", "by itself"),
    ("bad", "Adjective"): ("not good; unpleasant or harmful", "Too little sleep is bad for your health.", "not good; harmful"),
    ("blame", "Noun"): ("responsibility for a mistake or harmful event", "The driver accepted the blame for the accident.", "responsibility for a fault"),
    ("block", "Verb"): ("stop movement or prevent progress", "A fallen tree blocked the road.", "stop; prevent"),
    ("brilliant", "Adjective"): ("very clever, bright or excellent", "She had a brilliant idea for the project.", "excellent; very clever"),
    ("calculate", "Verb"): ("find an amount by using numbers", "We calculated the total cost of the trip.", "work out with numbers"),
    ("clothing", "Noun"): ("things people wear", "Bring warm clothing for the evening.", "clothes"),
    ("competitive", "Adjective"): ("wanting to win; involving people trying to win", "The two teams played a competitive match.", "eager to win"),
    ("contemporary", "Adjective"): ("belonging to the present time", "The museum displays contemporary art.", "modern; present-day"),
    ("contest", "Noun"): ("an event in which people try to win", "Our class entered a writing contest.", "competition"),
    ("continent", "Noun"): ("one of the world's main large land areas", "Africa is the second-largest continent.", "large land area"),
    ("copy", "Noun"): ("something made to be the same as another", "Please keep a copy of the form.", "duplicate"),
    ("criterion", "Noun"): ("a standard used to make a decision", "Price was an important criterion in our choice.", "standard"),
    ("decade", "Noun"): ("a period of ten years", "The city changed greatly during the last decade.", "ten-year period"),
    ("declare", "Verb"): ("announce something clearly or officially", "The judge declared the winner.", "announce officially"),
    ("degree", "Noun"): ("an amount or level; a university qualification", "The plan succeeded to a surprising degree.", "level; university qualification"),
    ("deliver", "Verb"): ("take something to a person or place; give a speech", "The company will deliver the package tomorrow.", "bring; present"),
    ("demanding", "Adjective"): ("needing a lot of time, effort or skill", "Teaching can be a demanding job.", "difficult; requiring effort"),
    ("detect", "Verb"): ("notice or discover something difficult to see", "The test can detect the disease early.", "discover; notice"),
    ("determine", "Verb"): ("discover or decide something", "The results will determine who reaches the final.", "decide; find out"),
    ("differ", "Verb"): ("be unlike or have another opinion", "The two plans differ in cost.", "be different"),
    ("disappointed", "Adjective"): ("sad because something was not as good as hoped", "We were disappointed by the result.", "sad; let down"),
    ("divide", "Verb"): ("separate into parts or groups", "Divide the class into four teams.", "separate"),
    ("domestic", "Adjective"): ("connected with one country or with the home", "Domestic flights are often shorter than international ones.", "national; related to home"),
    ("done", "Adjective"): ("finished or completed", "The work is done, so we can go home.", "finished"),
    ("double", "Adverb"): ("twice as much or as many", "This box weighs double the other one.", "twice as much"),
    ("double", "Verb"): ("make or become twice as much", "The school hopes to double the number of books.", "make twice as much"),
    ("economical", "Adjective"): ("using little money, fuel or time", "This small car is economical to run.", "not wasteful; low-cost"),
    ("editor", "Noun"): ("a person who prepares text, film or sound for publication", "The editor corrected the article before publication.", "person who prepares content"),
    ("element", "Noun"): ("a basic or important part", "Trust is an essential element of friendship.", "part; component"),
    ("emerge", "Verb"): ("come out or become known", "New facts emerged during the investigation.", "appear; come out"),
    ("emotion", "Noun"): ("a strong feeling such as joy, fear or anger", "Music can express deep emotion.", "feeling"),
    ("exception", "Noun"): ("a person or thing not included in a general rule", "Everyone arrived on time, with one exception.", "special case"),
    ("exchange", "Verb"): ("give one thing and receive another", "The students exchanged ideas after the talk.", "trade; swap"),
    ("expected", "Adjective"): ("believed or planned to happen", "The expected rain arrived in the afternoon.", "predicted; planned"),
    ("expedition", "Noun"): ("an organized journey for a special purpose", "The team went on an expedition to study the forest.", "organized journey"),
    ("expense", "Noun"): ("money needed or spent", "The hotel was our largest expense.", "cost"),
    ("export", "Noun"): ("goods sent to another country for sale", "Fruit is an important export for the region.", "goods sold abroad"),
    ("export", "Verb"): ("send goods to another country for sale", "The company exports fruit to Europe.", "sell abroad"),
    ("expression", "Noun"): ("a phrase; a way of showing a feeling or idea", "Her expression showed that she was surprised.", "phrase; show of feeling"),
    ("extend", "Verb"): ("make longer or larger; reach out", "The school extended the deadline by two days.", "lengthen; expand"),
    ("extreme", "Adjective"): ("very great, serious or far from normal", "Avoid exercise in extreme heat.", "very great; severe"),
    ("farther/further", "Adjective"): ("more distant or additional", "Please contact us if you need further information.", "more distant; additional"),
    ("farther/further", "Adverb"): ("to a greater distance or degree", "We walked farther than we had planned.", "more distantly; more"),
    ("fetch", "Verb"): ("go to get someone or something and bring them back", "Could you fetch a glass of water for me?", "go and bring"),
    ("final", "Noun"): ("the last game, test or stage in a series", "Our team reached the final.", "last stage"),
    ("fit", "Adjective"): ("healthy; suitable for a purpose", "She exercises every day to stay fit.", "healthy; suitable"),
    ("generation", "Noun"): ("people born at about the same time", "The younger generation uses technology differently.", "age group"),
    ("genuine", "Adjective"): ("real, honest or truly felt", "Her concern for the children was genuine.", "real; sincere"),
    ("hidden", "Adjective"): ("kept where it cannot easily be seen", "The key was hidden under a stone.", "not visible; secret"),
    ("highlight", "Verb"): ("make something seem especially important", "The report highlights the need for safer roads.", "emphasize"),
    ("historian", "Noun"): ("a person who studies and writes about the past", "The historian examined old letters.", "history expert"),
    ("historic", "Adjective"): ("important in the story of the past", "The leaders signed a historic agreement.", "important in history"),
    ("identical", "Adjective"): ("exactly the same", "The two bags look identical.", "exactly alike"),
    ("immigration", "Noun"): ("the movement of people into another country to live", "The museum tells the story of immigration to Israel.", "moving into a country"),
    ("import", "Noun"): ("goods brought into a country for sale", "Oil is a major import for many countries.", "goods bought abroad"),
    ("import", "Verb"): ("bring goods into a country for sale", "The shop imports coffee from Brazil.", "buy from abroad"),
    ("impress", "Verb"): ("make someone admire or notice something", "Her clear presentation impressed the judges.", "cause admiration"),
    ("impression", "Noun"): ("an idea or feeling formed about someone or something", "The school made a good impression on the visitors.", "opinion; feeling"),
    ("incredible", "Adjective"): ("very hard to believe; extremely good", "The view from the mountain was incredible.", "unbelievable; amazing"),
    ("infection", "Noun"): ("an illness caused by harmful organisms", "The doctor gave her medicine for the infection.", "illness from germs"),
    ("input", "Noun"): ("ideas, information or effort put into something", "The teacher asked students for input on the plan.", "ideas; information"),
    ("inside", "Adverb"): ("in or into an inner part", "It began to rain, so we went inside.", "within"),
    ("interaction", "Noun"): ("communication or activity between people or things", "Group work encourages interaction between students.", "communication; contact"),
    ("interpret", "Verb"): ("explain the meaning of something; translate speech", "Different readers may interpret the poem differently.", "explain; translate"),
    ("interrupt", "Verb"): ("stop someone briefly while they are speaking or working", "Please do not interrupt while she is answering.", "break in; disturb"),
    ("involvement", "Noun"): ("the act of taking part in something", "Parent involvement can help a school succeed.", "participation"),
    ("issue", "Noun"): ("an important subject or problem", "The class discussed the issue of online safety.", "topic; problem"),
    ("jam", "Noun"): ("a situation where movement is blocked; sweet fruit spread", "A traffic jam delayed the bus.", "blockage; fruit spread"),
    ("journalist", "Noun"): ("a person who reports news", "The journalist interviewed the mayor.", "news reporter"),
    ("judgment", "Noun"): ("an opinion or decision after careful thought", "Good judgment is important in an emergency.", "decision; opinion"),
    ("justice", "Noun"): ("fair treatment according to law or moral rules", "The family continued to fight for justice.", "fairness"),
    ("keen", "Adjective"): ("very interested, eager or sharp", "She is keen to improve her English.", "eager; enthusiastic"),
    ("keep", "Verb"): ("continue to have, stay in a condition or follow a rule", "Please keep your ticket until the end.", "hold; continue"),
    ("kit", "Noun"): ("a set of tools or equipment for a purpose", "Every car should have a first-aid kit.", "equipment set"),
    ("learn", "Verb"): ("gain knowledge or skill", "Children learn new words through reading.", "gain knowledge"),
    ("lecture", "Noun"): ("a formal educational talk", "We attended a lecture about space.", "formal talk"),
    ("lecture", "Verb"): ("give a formal educational talk", "She lectures on modern history at the university.", "give a formal talk"),
    ("light", "Verb"): ("make something begin to burn or become bright", "Please light the candle carefully.", "set on fire; brighten"),
    ("living", "Noun"): ("money earned for basic needs; a way of life", "She earns a living as a designer.", "income; way of life"),
    ("logical", "Adjective"): ("based on clear and sensible thinking", "Your explanation is simple and logical.", "reasonable; sensible"),
    ("lower", "Verb"): ("move down or make less", "The store lowered its prices.", "reduce; move down"),
    ("mend", "Verb"): ("repair something that is broken or damaged", "Can you mend this torn shirt?", "repair"),
    ("mixture", "Noun"): ("a combination of different things", "The soup is a mixture of vegetables and spices.", "combination"),
    ("monthly", "Adjective"): ("happening or produced once a month", "We have a monthly team meeting.", "every month"),
    ("mystery", "Noun"): ("something difficult or impossible to explain", "The cause of the noise remains a mystery.", "unexplained event"),
    ("name", "Verb"): ("give a title to or identify", "They named the new library after a local writer.", "identify; give a title"),
    ("native", "Adjective"): ("connected with the place where someone was born", "Hebrew is her native language.", "from one's birthplace"),
    ("nightmare", "Noun"): ("a frightening dream or very unpleasant situation", "Missing the last train was a nightmare.", "bad dream; terrible situation"),
    ("nonsense", "Noun"): ("words or ideas with no meaning or truth", "The rumor was complete nonsense.", "meaningless talk"),
    ("occupation", "Noun"): ("a job; the act of using or controlling a place", "Please write your occupation on the form.", "job; control of a place"),
    ("occupy", "Verb"): ("use, fill or take control of a space or time", "The sofa occupies most of the room.", "fill; take up"),
    ("oil", "Noun"): ("a thick liquid used as fuel, food or machine protection", "Heat a little oil in the pan.", "fatty liquid; fuel"),
    ("open", "Verb"): ("make something no longer closed; begin operating", "Please open the window.", "unclose; begin"),
    ("operate", "Verb"): ("control a machine; perform medical treatment", "Only trained staff may operate the machine.", "run; control"),
    ("organ", "Noun"): ("a body part with a special job; a large musical instrument", "The heart is a vital organ.", "body part; musical instrument"),
    ("organization", "Noun"): ("an official group; the act of arranging things", "She works for an international organization.", "group; arrangement"),
    ("outstanding", "Adjective"): ("extremely good; not yet completed or paid", "She received an award for outstanding work.", "excellent; unfinished"),
    ("patient", "Adjective"): ("able to wait calmly", "Please be patient while the page loads.", "calm while waiting"),
    ("peculiar", "Adjective"): ("strange or unusual", "There was a peculiar smell in the room.", "strange"),
    ("place", "Noun"): ("a particular area, position or point", "This quiet place is perfect for reading.", "location; position"),
    ("point", "Noun"): ("an idea, purpose, score or exact place", "The speaker made an important point.", "idea; purpose; score"),
    ("point", "Verb"): ("show a direction with a finger or object", "She pointed to the correct answer.", "indicate"),
    ("position", "Noun"): ("a place, job or opinion", "He applied for a teaching position.", "location; job; opinion"),
    ("potential", "Noun"): ("the ability to develop or succeed in the future", "The young player has great potential.", "future ability"),
    ("preference", "Noun"): ("a greater liking for one choice", "She expressed a preference for the morning class.", "choice; greater liking"),
    ("present", "Verb"): ("show, give or formally introduce something", "Each group will present its project tomorrow.", "show; introduce"),
    ("pressure", "Noun"): ("force; worry caused by demands", "Students often feel pressure before exams.", "force; stress"),
    ("prime", "Adjective"): ("main or most important", "Safety is our prime concern.", "main; most important"),
    ("principal", "Adjective"): ("main or most important", "The principal reason for the delay was heavy traffic.", "main"),
    ("principal", "Noun"): ("the head of a school", "The principal welcomed the new students.", "school head"),
    ("promote", "Verb"): ("support, advertise or move someone to a higher job", "The campaign promotes healthy eating.", "encourage; advertise; advance"),
    ("reach", "Noun"): ("the distance that someone can touch or influence", "Keep the medicine out of children's reach.", "touching distance"),
    ("reach", "Verb"): ("arrive at or stretch far enough to touch", "We reached the station before noon.", "arrive; extend"),
    ("reason", "Noun"): ("a cause or explanation for an action or event", "What was the reason for the change?", "cause; explanation"),
    ("record", "Noun"): ("stored information; the best result achieved", "The school keeps a record of attendance.", "saved information; best result"),
    ("record", "Verb"): ("store sound, pictures or information", "Students recorded a short interview.", "save information"),
    ("reflect", "Verb"): ("show an image; show or think deeply about something", "The results reflect the students' hard work.", "show; consider"),
    ("register", "Noun"): ("an official list of names or information", "The teacher checked the class register.", "official list"),
    ("register", "Verb"): ("put a name or information on an official list", "You must register before the course begins.", "sign up"),
    ("regret", "Noun"): ("sadness about something done or missed", "Her only regret was leaving too early.", "sad feeling"),
    ("regret", "Verb"): ("feel sorry about something", "I regret not asking for help sooner.", "feel sorry"),
    ("relate", "Verb"): ("connect things; understand someone's experience", "The examples relate directly to the topic.", "connect; understand"),
    ("relax", "Verb"): ("rest and become less worried", "I like to relax by reading.", "rest; become calm"),
    ("remark", "Noun"): ("a spoken or written comment", "His final remark made everyone laugh.", "comment"),
    ("remark", "Verb"): ("say or write a comment", "She remarked that the room was unusually quiet.", "comment"),
    ("remote", "Adjective"): ("far away; controlled from a distance", "They live in a remote mountain village.", "distant"),
    ("replace", "Verb"): ("put one person or thing instead of another", "We need to replace the broken chair.", "substitute"),
    ("rescue", "Noun"): ("an act of saving someone from danger", "The rescue took several hours.", "saving from danger"),
    ("rescue", "Verb"): ("save someone from danger", "Firefighters rescued the family.", "save"),
    ("respect", "Noun"): ("admiration or polite treatment", "The students showed respect for one another.", "admiration; politeness"),
    ("respect", "Verb"): ("admire or treat someone well", "We should respect different opinions.", "admire; treat well"),
    ("retire", "Verb"): ("stop working because of age or after a long career", "She plans to retire next year.", "leave work permanently"),
    ("right", "Adjective"): ("correct, suitable or on the side opposite left", "You chose the right answer.", "correct; suitable"),
    ("role", "Noun"): ("a function, duty or acting part", "Parents play an important role in education.", "function; part"),
    ("room", "Noun"): ("a part of a building; available space", "There is enough room for one more chair.", "indoor space; capacity"),
    ("rough", "Adjective"): ("not smooth; difficult or violent", "The sea was rough during the storm.", "uneven; difficult"),
    ("rule", "Noun"): ("an official instruction about what is allowed", "The school has a rule against running indoors.", "instruction; regulation"),
    ("rule", "Verb"): ("control or govern a country or group", "The queen ruled the country for many years.", "govern"),
    ("run", "Verb"): ("move quickly on foot; manage or operate", "She runs a small bookshop.", "move fast; manage"),
    ("rush", "Noun"): ("a sudden quick movement or very busy period", "There was a morning rush at the station.", "hurry; busy time"),
    ("rush", "Verb"): ("move or act very quickly", "Do not rush your answer.", "hurry"),
    ("satisfy", "Verb"): ("meet a need or make someone pleased", "The solution satisfied everyone.", "please; meet a need"),
    ("scale", "Noun"): ("a set of levels; a device for measuring weight", "Rate each answer on a scale from one to five.", "range; measuring device"),
    ("scene", "Noun"): ("a part of a play or film; the place of an event", "The final scene of the film was moving.", "part of a story; event place"),
    ("schedule", "Noun"): ("a plan showing times for activities", "The train arrived according to schedule.", "timetable"),
    ("sensitive", "Adjective"): ("easily affected; needing careful treatment", "This is a sensitive subject for many people.", "easily affected; delicate"),
    ("service", "Noun"): ("work or help provided for people", "The hotel offers a free bus service.", "assistance; public provision"),
    ("set", "Verb"): ("put in a place; decide or fix a time or level", "We set a date for the next meeting.", "place; fix"),
    ("setting", "Noun"): ("the place and time of an event or story", "The village is the setting of the novel.", "surroundings; background"),
    ("shortly", "Adverb"): ("soon; in a few words", "The train will arrive shortly.", "soon; briefly"),
    ("similarity", "Noun"): ("a way in which people or things are alike", "There is a clear similarity between the two designs.", "likeness"),
    ("society", "Noun"): ("people living together in an organized community", "Technology has changed modern society.", "community"),
    ("spectacular", "Adjective"): ("very impressive or beautiful", "We watched a spectacular sunset.", "impressive; amazing"),
    ("speech", "Noun"): ("a formal talk; the ability to speak", "The student gave a short speech at the ceremony.", "formal talk; speaking"),
    ("spoil", "Verb"): ("damage or ruin; give someone too much", "Do not let the rain spoil the picnic.", "ruin"),
    ("style", "Noun"): ("a particular way of doing, writing or designing", "The writer has a clear and simple style.", "manner; design"),
    ("summary", "Noun"): ("a short statement of the main points", "Write a brief summary of the article.", "short account"),
    ("support", "Noun"): ("help, agreement or something that holds an object", "The student received support from her teacher.", "help; backing"),
    ("support", "Verb"): ("help, agree with or hold up", "Her family supported her decision.", "help; back"),
    ("survive", "Verb"): ("continue to live or exist after danger", "Few plants can survive without water.", "stay alive"),
    ("theme", "Noun"): ("the main subject or idea", "Friendship is the central theme of the story.", "main idea"),
    ("treasure", "Noun"): ("valuable objects or something greatly loved", "The divers found an ancient treasure.", "valuable collection"),
    ("try", "Noun"): ("an attempt to do something", "Give the question another try.", "attempt"),
    ("turn", "Noun"): ("a change of direction; a person's time to act", "It is your turn to answer.", "change; chance in order"),
    ("uncomfortable", "Adjective"): ("not relaxed, pleasant or physically easy", "The chair was hard and uncomfortable.", "not comfortable; uneasy"),
    ("understand", "Verb"): ("know the meaning or reason", "I understand the instructions now.", "comprehend"),
    ("undo", "Verb"): ("reverse an action; open something tied or fastened", "Click this button to undo the last change.", "reverse; unfasten"),
    ("unemployed", "Adjective"): ("without a paid job", "He was unemployed for three months.", "without work"),
    ("unexpected", "Adjective"): ("not planned or believed likely to happen", "An unexpected guest arrived at dinner time.", "surprising; unplanned"),
    ("urgent", "Adjective"): ("needing immediate attention", "The doctor received an urgent call.", "immediate; pressing"),
    ("vowel", "Noun"): ("a speech sound represented by letters such as a, e, i, o or u", "The word 'cat' contains one vowel.", "a, e, i, o or u sound"),
    ("waste", "Adjective"): ("not wanted and left after use", "The factory turns waste material into fuel.", "unwanted; leftover"),
    ("waste", "Verb"): ("use badly or use more than needed", "Do not waste clean water.", "use carelessly"),
    ("wealth", "Noun"): ("a large amount of money, property or useful things", "The country has a wealth of natural resources.", "riches; abundance"),
    ("welcome", "Adjective"): ("wanted and giving pleasure", "The cool rain was a welcome change.", "pleasing; wanted"),
    ("welcome", "Verb"): ("greet someone with pleasure", "Students welcomed the new teacher.", "greet warmly"),
})


def load_defs(word: str) -> list[tuple[str, str]]:
    path = DATAMUSE / f"{word.casefold()}.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not payload or payload[0].get("word", "").casefold() != word.casefold():
        return []
    result = []
    for raw in payload[0].get("defs", []):
        if "\t" not in raw:
            continue
        tag, definition = raw.split("\t", 1)
        lower_raw = definition.casefold()
        if any(
            label in lower_raw
            for label in [
                "archaic",
                "obsolete",
                "heraldry",
                "mathematics",
                "chemistry",
                "programming",
                "surname",
                "given name",
                "nautical",
                "slang",
                "dialectal",
            ]
        ):
            continue
        definition = re.sub(r"\([^)]*\)", "", definition)
        definition = re.sub(r"\s+", " ", definition).strip(" .;")
        result.append((tag, definition))
    return result


POS_TAGS = {"Noun": "n", "Verb": "v", "Adjective": "adj", "Adverb": "adv"}


def simple_definition(display: str, pos: str, meanings: list[str]) -> str:
    phrase = PHRASES.get(display.casefold())
    if phrase:
        return phrase[1]
    special = FUNCTION_WORDS.get((display.casefold(), pos))
    if special:
        return special[1]
    curated = CURATED.get((display.casefold(), pos))
    if curated:
        return curated[0]
    gloss = MULTI_POS_GLOSSES.get((display.casefold(), pos))
    if gloss:
        if ";" in gloss:
            return gloss
        return gloss
    target = display.casefold()
    for meaning in meanings:
        clean = re.sub(r"\([^)]*\)", "", meaning).strip(" .;")
        if clean and target not in clean.casefold() and len(clean.split()) <= 16:
            return clean
    tag = POS_TAGS.get(pos)
    candidates = []
    if re.fullmatch(r"[A-Za-z-]+", display):
        for def_tag, definition in load_defs(display):
            if tag and def_tag != tag:
                continue
            lower_definition = definition.casefold()
            if re.search(rf"\b{re.escape(target)}\w*\b", lower_definition):
                continue
            stem = re.sub(r"[^a-z]", "", target)[:5]
            if len(stem) >= 5 and stem in re.sub(r"[^a-z]", "", lower_definition):
                continue
            words = definition.split()
            if 2 <= len(words) <= 20:
                candidates.append(definition)
    if candidates:
        return candidates[0].removeprefix("To ").removeprefix("A ").removeprefix("An ")
    fallbacks = {
        "Noun": "a person, thing, idea or event connected with this subject",
        "Verb": "do this action or make this change",
        "Adjective": "having this quality or condition",
        "Adverb": "in this way or at this time",
        "Preposition": "used to show a relation between people, things, places or times",
        "Conjunction": "used to connect words, ideas or events",
        "Pronoun": "used instead of a noun or name",
        "Auxiliary verb": "used with another verb",
    }
    return fallbacks.get(pos, "a group of words with this meaning")


def hebrew_source(display: str, pos: str, meanings: list[str]) -> str:
    phrase = PHRASES.get(display.casefold())
    if phrase:
        return phrase[0]
    special = FUNCTION_WORDS.get((display.casefold(), pos))
    if special:
        return special[0]
    curated = CURATED.get((display.casefold(), pos))
    if curated:
        return curated[2]
    gloss = MULTI_POS_GLOSSES.get((display.casefold(), pos))
    if gloss:
        return gloss
    for meaning in meanings:
        if meaning and len(meaning.split()) <= 8:
            return meaning
    if pos == "Verb":
        return f"to {display}"
    return display


INTRANSITIVE = {
    "appear", "cope", "decrease", "differ", "emerge", "exist", "go out", "react", "relax", "retire",
    "run", "rush", "survive", "vary",
}


def example(display: str, pos: str) -> str:
    phrase = PHRASES.get(display.casefold())
    if phrase:
        return phrase[2]
    special = FUNCTION_WORDS.get((display.casefold(), pos))
    if special:
        return special[2]
    curated = CURATED.get((display.casefold(), pos))
    if curated:
        return curated[1]
    word = display
    if pos == "Noun":
        return f"The {word} affected the final decision."
    if pos == "Verb":
        if display.casefold() in INTRANSITIVE:
            return f"Things may {word} when the situation changes."
        return f"They decided to {word} the issue carefully."
    if pos == "Adjective":
        return f"The situation seemed {word} to everyone."
    if pos == "Adverb":
        return f"She explained the idea {word}."
    return f"The teacher used {word} in a clear sentence."


def main() -> None:
    if not HEBREW_GLOSSES.exists():
        raise SystemExit(f"Missing reviewed Hebrew glosses: {HEBREW_GLOSSES}")
    hebrew_glosses = json.loads(HEBREW_GLOSSES.read_text(encoding="utf-8"))
    rows_by_list = {letter: vocab.load_official_rows(letter) for letter in "AB"}
    cards = {letter: vocab.merge_official_cards(rows_by_list[letter]) for letter in "AB"}
    official = {
        (card["list"], vocab.key_text(card["display"]), card["pos"]): card
        for letter in "AB"
        for card in cards[letter]
    }
    with vocab.CONTENT_TSV.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    for row in rows:
        key = (row["List"], vocab.key_text(row["Display"]), row["POS"])
        card = official[key]
        row["Hebrew source"] = hebrew_glosses[
            f"{card['list']}|{card['display'].casefold()}|{card['pos']}"
        ]
        row["A2 definition or synonyms"] = simple_definition(
            row["Display"], row["POS"], card["official_meanings"]
        )
        row["English example"] = example(row["Display"], row["POS"])
    with vocab.CONTENT_TSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=rows[0].keys(), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Autofilled {len(rows)} A/B card rows in {vocab.CONTENT_TSV}")


if __name__ == "__main__":
    main()
