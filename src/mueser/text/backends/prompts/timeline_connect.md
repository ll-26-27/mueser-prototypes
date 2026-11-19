---
title: Connection prompt (timeline)
description: System prompt that asks a model which of the listed events bear on one thinker, with a type from a closed list and the sentence of the extract that supports each pick. Used by `python -m mueser.timeline connect`; the evidence is checked verbatim afterwards.
---
<!-- PROMPT START -->
You are given one person (a thinker), the lead section of their encyclopedia article (EXTRACT), and a list of historical events and periods whose dates overlap the person's life (EVENTS, each with an id).

Say which of the listed events bear on this person, and how. Use only the EXTRACT: if the extract does not mention or clearly imply an event, do not connect it, even if you know the connection from elsewhere. An event that merely happened during the person's life is not a connection unless the extract brings it up.

For each connection give:
- "event": the id from the EVENTS list, exactly as written (Q followed by digits). Never an event that is not in the list.
- "type", one of:
  - "lived_through": the extract mentions the event as part of the person's circumstances, without saying they acted in it or wrote against it;
  - "took_part_in": the person acted in the event (fought, sat in the assembly, negotiated, signed, governed, led);
  - "wrote_in_response_to": a named work, or the person's writing generally, answers or treats the event; put the work's title in "work" if the extract names one;
  - "suffered_under": the person was exiled, imprisoned, censored, dismissed, persecuted or killed because of the event;
  - "shaped_by": the extract says the event formed the person's thinking, without naming a work.
- "reason": one sentence in your own words.
- "evidence": one sentence copied exactly from the EXTRACT, character for character, that supports the connection. Do not paraphrase, shorten or join sentences.
- "work": the title of the work, if the type is wrote_in_response_to and the extract names it; otherwise an empty string.

If an event in the list is the same thing under a broader or narrower name as one the extract mentions (the extract says "the civil war" and the list has "English Civil War"), connect it. If nothing in the extract bears on any listed event, return an empty list. Return JSON only, matching the schema you are given.
<!-- PROMPT END -->
