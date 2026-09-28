'use strict';
// A deliberately small, traceable Band III pilot. A1–A3 are GROUPS, not difficulty levels.
const source = {
  repository: 'Simonh68/module-e-vocab',
  commit: '912053cc5030cd6be4a936e642f34775fd07fb67',
  tsv: {path:'data/ab_content.tsv', blob:'ef5a0f07450c4f7d96985846579271a8e982c227'},
  master: {path:'data/vocabulary-master.json', blob:'89ee7153930a5e5e04f92485a22f63ba24a9d38b'},
  note: 'Definitions, examples, POS and IDs are source-derived. Context clues and pair missions are newly authored pilot content; they are not an official examination.'
};
const raw = [
 ['A3-038','analysis','Noun','careful study of parts or information','The report includes an analysis of the results.','ניתוח','The researchers compared all the results carefully. Which noun names this careful study?'],
 ['A1-001','proof','Noun','information showing that something is true','The photo provided proof of the damage.','הוכחה; ראיה','Someone doubts that the window was damaged. A clear photo can provide this.'],
 ['A3-070','claim','Verb','say that something is true','The company claims that the product is safe.','לטעון','Without presenting evidence, the company says its product is the safest. Which verb describes what it does?'],
 ['A1-072','challenge','Verb','question or disagree with something','The student challenged the speaker’s claim.','לערער על','A listener questions whether a speaker’s statement is true. Which verb describes this action?'],
 ['A1-013','conduct','Verb','organize and carry out','The class conducted a short survey.','לנהל; לערוך','The students organize a survey and carry it out. Which verb describes what they do?'],
 ['A2-051','approach','Noun','a way of doing or thinking about something','This teaching approach helps beginners.','גישה','Two teachers use different ways to teach the same topic. Each teacher has a different ___.'],
 ['A3-014','considerable','Adjective','large or important','The project required considerable effort.','ניכר; רב','The project takes a large amount of effort, not just a little. The effort is ___.'],
 ['A1-002','advance','Noun','movement forward; progress','The team made an important advance in its research.','התקדמות','A research team moves forward and makes progress. Which noun names this progress?'],
 ['A1-047','advertising','Noun','messages that try to sell products','Online advertising can reach many people.','פרסום','A company pays for messages designed to make people buy a product. What is this activity called?'],
 ['A3-058','critic','Noun','a person who judges or gives opinions','The film critic wrote a positive review.','מבקר','A person watches films and writes reviews that judge their quality. What is this person called?'],
 ['A3-048','characteristic','Noun','a usual or special quality','Patience is an important characteristic of a good teacher.','מאפיין; תכונה','Patience is a quality that helps describe a good teacher. Which noun names such a quality?'],
 ['A3-007','consequence','Noun','a result of an action or event','One consequence of the storm was a power cut.','תוצאה; השלכה','A storm causes a power cut. The power cut is a ___ of the storm.'],
 ['A3-032','conditions','Noun','the situation in which people or things exist','The workers asked for safer conditions.','תנאים; נסיבות','The workers need a safer situation in which to do their jobs. They ask for better working ___.'],
 ['A2-008','complicated','Adjective','difficult to understand or deal with','The instructions seemed complicated at first.','מסובך; מורכב','The instructions have many connected steps and are difficult to understand. They are ___.'],
 ['A1-036','cope','Verb','deal successfully with something difficult','She learned to cope with the pressure.','להתמודד','She learns to deal successfully with a difficult situation. She learns to ___ with it.'],
 ['A2-031','current','Adjective','happening or existing now','The article describes the current situation.','נוכחי','The article describes the situation that exists now, not the one from last year. It describes the ___ situation.']
];
const words = raw.map(([id,en,pos,definition,example,he,context])=>({id,en,pos,definition,example,he,context,group:id.split('-')[0],sourceFile:id==='A1-001'?source.master.path:source.tsv.path}));
const pairs = [
 {ids:['A3-038','A1-001'],title:'Check the evidence',clue:'A report needs TWO things: a careful study of its results, and information showing that its main statement is true.'},
 {ids:['A3-070','A1-072'],title:'A lively debate',clue:'Choose TWO verbs: one means to say that something is true; the other means to question or disagree with that statement.'},
 {ids:['A1-013','A2-051'],title:'Plan a study',clue:'Choose a VERB meaning to organize and carry out a survey, and a NOUN meaning a way of doing the work.'},
 {ids:['A3-014','A1-002'],title:'Make progress',clue:'Choose an ADJECTIVE meaning large or important, and a NOUN meaning movement forward or progress.'},
 {ids:['A1-047','A3-058'],title:'A film launch',clue:'Choose the activity that uses messages to sell a film, and the person who judges the film and writes a review.'},
 {ids:['A3-048','A3-007'],title:'Quality or result?',clue:'Find TWO nouns: a usual or special quality of something, and a result of an action or event.'},
 {ids:['A3-032','A2-008'],title:'A difficult project',clue:'Choose the NOUN for the situation in which people work, and the ADJECTIVE for a task that is difficult to understand.'},
 {ids:['A1-036','A2-031'],title:'Face today’s challenge',clue:'Choose a VERB meaning to deal successfully with difficulty, and an ADJECTIVE meaning happening or existing now.'}
];
module.exports = {source,words,pairs};
