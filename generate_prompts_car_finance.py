import json
import requests

# --- IMAGE PROMPTS ---

PREFIX = "2D colourful whiteboard animation style. Clean white background. All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. 16:9 widescreen aspect ratio, landscape composition."
SUFFIX = "Bold colourful hand-drawn illustration."

MONKEY_SCENES = {
    "0.1", "0.3", "0.11", "1.1", "1.7", "2.1", "3.4", "3.9", "3.14", "3.22",
    "3.26", "3.29", "3.32", "3.35", "3.41", "3.46", "3.49", "3.51", "3.54",
    "3.57", "3.62", "4.3", "4.5", "5.2", "5.4"
}

image_scenes = {
    "0.1": "A cheerful monkey in a cartoon car dealership showroom, pressing a pen to a PCP contract on a desk on the left. On the right, David stands at a separate desk signing a personal loan form. Both face a Ford Puma illustration between them. Monkey is mid-signing with pen in hand.",
    "0.2": "Split-screen: Sarah on the left with a smug grin and a thought bubble showing a thumbs-up. David on the right with a confident nod and a thought bubble showing a thumbs-up. A question mark hovers above both thought bubbles.",
    "0.3": "A monkey holding a large magnifying glass over a spreadsheet showing two columns of numbers. The gap between the two columns is highlighted with a bold red arrow. Numbers '£28,000' written in bold blue marker on the canvas.",
    "0.4": "A bold illustration of a Ford Puma in the centre. Text '£28,000' written in large bold red hand-drawn letters below it. Sarah stands to the left and David to the right, both looking at the car. Dashed vertical line separating them.",
    "0.5": "Sarah standing beside a PCP contract form. Bold hand-drawn text '£2,800 deposit' and '£375/month' written in red and blue marker on the canvas beside her. A calendar showing '36 months' is sketched in the corner.",
    "0.6": "A slick finance manager in a car dealership sliding a contract across a desk towards Sarah. A speech bubble from the manager reads 'Great deal!' Sarah looks pleased. Stars and sparkles around the phrase 'full warranty'.",
    "0.7": "Illustration of a contract tied up with a ribbon labelled 'Simple. Clean.' A pair of scissors is hovering nearby but not cutting. A subtle shadow underneath the ribbon hints at hidden strings.",
    "0.8": "David standing beside a loan agreement. Hand-drawn text '£3,000 deposit', '£25,000 loan', '7.5% APR', '£501/month' written in bold marker on the canvas. A bold red circle around '£501'. A smaller note '£126 more than Sarah' written underneath.",
    "0.9": "Close-up of David's face with a focused, slightly uneasy expression. A thought bubble shows '£375' on one side and '£501' on the other with an arrow pointing at the gap labelled '+£126'. No mouth movement implied.",
    "0.10": "Sarah driving a shiny Ford Puma off a forecourt, beaming. A 'Day 1' banner above. David watches from the pavement, arms folded, looking slightly less enthused. Sunshine and sparkles around Sarah's car.",
    "0.11": "A monkey pointing at a large diagram showing two structures: PCP on the left as a rental loop arrow, and a personal loan on the right as a straight line with a finish flag. The monkey holds a pointer stick, looking curious.",
    "0.12": "Split-screen: left side shows Sarah with coins floating away from her labelled 'Renting'. Right side shows David with coins stacking up labelled 'Buying'. Hand-drawn pound signs decorating both sides.",
    "0.13": "A large clock with a bold arrow showing time passing. Two bar charts side by side — one growing taller on David's side, one staying flat on Sarah's side. Hand-drawn '£thousands' label on the vertical axis.",

    "1.1": "A monkey lounging happily in a brand new car interior. Air freshener shaped like a tree swings from the mirror. 'NEW CAR SMELL' written in swirly letters in a speech bubble. Monkey holds the steering wheel with one hand looking relaxed.",
    "1.2": "Three comic-panel style illustrations side by side: a broken engine with 'COVERED' stamp, brake pads with 'COVERED' stamp, and a broken AC unit with 'COVERED' stamp. All with bold green tick marks.",
    "1.3": "Sarah walking past a row of bill envelopes all stamped 'VOID' or 'COVERED'. She's smiling, hands in pockets. Clean and uncluttered background.",
    "1.4": "David looking at his car with a thought bubble showing a downward depreciation graph. Hand-drawn '£501/month' written in red on the canvas. His expression is slightly grim but determined.",
    "1.5": "A Ford Puma illustration with three price tags: '£28,000' at purchase, '£24,000' at end of Day 1, '£21,000' at Year 1. Bold downward red arrows connecting each price. Labels 'Day 1', 'Year 1' written in marker.",
    "1.6": "Two parallel bars: one showing 'Car Value' dropping to '£18,000' at Year 2, one showing 'Loan Balance' still at '£20,000'. The loan bar is taller — drawn in red. Bold '£18,000' and '£20,000' written in hand-drawn marker.",
    "1.7": "A monkey standing at the edge of a large hole in the ground labelled 'UNDERWATER'. David's silhouette is visible below looking up. The monkey peers down with a worried expression, holding a rope. '£2,000 underwater' written in red on the canvas.",
    "1.8": "Sarah watching David from across a street, arms folded knowingly. A thought bubble above her reads 'I made the right call.' A subtle smirk. David in the background next to his car looking stoic.",

    "2.1": "A monkey with a calculator in one hand and a pen in the other, writing on a large canvas. Left column: 'Sarah — £2,800 + 36 × £375 = £16,300' written in bold blue marker. Monkey mid-calculation pose.",
    "2.2": "Right column continues: 'David — £3,000 + 36 × £501 = £21,036' written in bold red marker on the canvas. A bold underline beneath both totals for emphasis.",
    "2.3": "A scoreboard-style illustration showing 'Sarah: £16,300' vs 'David: £21,036'. A bold arrow pointing at Sarah's lower number with 'Winning?' written next to it. But a large question mark hovers over the whole board. Hand-drawn '£5,000' gap labelled with a bracket.",

    "3.1": "Sarah driving back to a dealership. Three signpost arrows on a post in front of her labelled '1. Pay Balloon', '2. Hand Keys Back', '3. New PCP'. Sarah looks at the signpost, one hand on her chin thinking.",
    "3.2": "Bold hand-drawn text '£12,000 Balloon' in large red marker on the canvas. A receipt below it totalling '£28,300'. A shocked face expression beside it.",
    "3.3": "Sarah handing car keys back over a counter to a dealership manager. A big pile of receipts behind her labelled '£16,300'. An 'X' in red over the pile labelled 'Gone'. Sad expression on Sarah.",
    "3.4": "A monkey on a conveyor belt stretching off to the right. Each step on the belt is labelled: 'New Deal', 'Payments', 'Return', 'New Deal', 'Payments'. Monkey looks dizzy but keeps moving. A circular arrow above labelled 'Repeat'.",
    "3.5": "A new car with a fresh odometer showing '0'. Next to it, a payment counter still running, showing '£375/month'. A split graphic: odometer reset arrow pointing left, payment counter arrow pointing right.",
    "3.6": "A calendar with Month 36 circled in green. David pointing at it confidently. A loan balance meter showing '24 payments remaining' drawn in hand-drawn style. Bold '24' circled in blue marker.",
    "3.7": "David walking along a path of steps, each step labelled with a payment number: '37', '38', '39'… A flag at the end labelled 'OWNED'. Bold arrow pointing toward the flag.",
    "3.8": "Split-screen: Sarah's path leads to a revolving door back to the dealership (labelled 'Start Over'). David's path leads to a finish line flag labelled 'Done'. Dashed vertical line between them.",
    "3.9": "A monkey holding two signs side by side. Left sign shows a circular conveyor belt with 'PCP'. Right sign shows a straight line with a flag at the end labelled 'Buy'. Monkey points to the difference with a pointer. Bold arrow highlighting the finish line.",
    "3.10": "A large calendar with Month 60 circled in bold green. David standing beside it, fist raised in celebration. A 'PAID IN FULL' stamp across his loan document. Confetti around him.",
    "3.11": "David's car on his driveway. Three small icons below: an insurance shield, a fuel pump, and a spanner — all connected by a simple line. Text underneath: 'That's it.' Bold and simple illustration.",
    "3.12": "A simple monthly cost chart showing 'Insurance + Fuel + Maintenance = £70–£100/month' written in bold hand-drawn marker. Clean infographic style with a green tick.",
    "3.13": "Sarah sitting in her car with a payment reminder notification on her phone showing '£375'. Her expression is neutral — this is just normal life now. Calendar behind her shows Month 61.",
    "3.14": "A monkey reading a newspaper with the headline 'MONTHLY PAYMENT IS JUST NORMAL NOW'. Monkey holds a coffee mug. A subtle red warning sign in the corner labelled 'DANGER'. Monkey's expression is blissfully unaware.",
    "3.15": "A scoreboard illustration labelled 'End of Year 6'. Two columns: Sarah and David. Numbers being written in bold red and blue marker. A bold 'VS' between them.",
    "3.16": "Two receipts side by side for Sarah. Receipt 1: '£2,800 + £13,500 = £16,300'. Receipt 2: '£2,800 + £13,500 = £16,300'. Grand total: '£32,600' written in large bold red marker at the bottom. Stacked receipt illustration.",
    "3.17": "Sarah standing with empty hands and a shocked expression. Behind her: a pile of receipts. In front of her: nothing. An empty driveway. Bold text 'Zero Assets' in red hand-drawn marker.",
    "3.18": "David's total receipt: '£3,000 + £30,060 = £33,060' written in bold blue hand-drawn marker. Receipt paper curling at the edges. Underlined total.",
    "3.19": "David standing next to his car with a 'OWNED' badge on it. Two value tags on the car: '£9,000–£11,000'. Zero monthly payment counter below showing '£0/month'. Bold green '£0' in marker.",
    "3.20": "A simple maths illustration: '£33,060 − £10,000 (asset) = ~£23,000 effective cost'. Each number written in hand-drawn bold marker. A large equals sign in blue.",
    "3.21": "Sarah's column: '£32,600 spent' in red, then 'Assets: £0' in red below it, both hand-drawn large on canvas.",
    "3.22": "A monkey pointing at a scoreboard. Sarah's side: '£32,600 / Zero'. David's side: '~£23,000 / Car worth £10k'. Monkey's expression: wide-eyed and amazed. Bold red circle around the asset column.",
    "3.23": "A large seesaw/balance illustration. Left side (Sarah) is heavier — weighed down by receipts. Right side (David) is lighter — balanced by a car icon. Bold red 'THE FLIP' label written above the seesaw.",
    "3.24": "A finance manager's hand sliding a small card across a desk showing '£375/month'. The rest of the desk is hidden under a black curtain with a 'CONDITIONS' label. Bold red '£375' on the card.",
    "3.25": "Close-up of an advertisement showing '£375/month' in giant bold text. Below in tiny font: 'T&Cs apply'. The tiny text is circled in red with an arrow and a question mark.",
    "3.26": "A monkey unrolling a long scroll labelled 'CONDITIONS'. Items listed: 'Mileage Cap', 'Condition Charges', 'GAP Insurance', 'Early Exit Fees'. Monkey looks surprised at the length of the scroll.",
    "3.27": "A speedometer with a mileage counter showing '10,000 miles/year' cap drawn in red. An arrow going past the cap labelled 'OVER'. Below: '8–15p per mile' written in bold red hand-drawn marker.",
    "3.28": "Bold hand-drawn text '8–15p per mile' and '3,000 miles over = up to £450' written on the canvas. A surprise billing envelope with a shocked face popping out of it.",
    "3.29": "A monkey receiving a large bill envelope at the end of a contract. The envelope is labelled 'SURPRISE'. Monkey holds it at arm's length with a look of horror. '£450' written in large red marker on the envelope.",
    "3.30": "A car being inspected by a dealer with a clipboard. Close-up of a small scuff on the bumper circled in red. A magnifying glass over it. An ominous shadow looming over the scene.",
    "3.31": "Three damage close-ups: bumper scuff, interior mark, cracked alloy — each with a red circle and a price tag: '£250+'. A dealer stamping 'CHARGEABLE' on each one.",
    "3.32": "A monkey sitting across from a finance manager in a dealership. The manager slides a GAP insurance brochure across the desk labelled '£350'. Monkey eyes the brochure sceptically. Bold '£350' in red marker on the brochure.",
    "3.33": "A totalled car being towed away on the left. An insurance payout cheque on the right that's visibly smaller than the outstanding finance amount. A red gap between the two amounts labelled 'THE GAP'.",
    "3.34": "A credit card with the text 'Section 75 CCA' on it, surrounded by a protective shield. Bold hand-drawn text 'Already Protected?' written in blue marker. The shield glows green.",
    "3.35": "A monkey holding two price tags: one from a dealer showing '£350 GAP' and one from an independent provider showing '£80 GAP'. Monkey points to the cheaper one with a big thumbs-up. Bold price numbers in marker.",
    "3.36": "Sarah holding a PCP contract with a large padlock icon on top. Around her: icons of life changes — moving box, baby pram, briefcase with 'REDUNDANT' stamp. Arrows all pointing at the locked contract.",
    "3.37": "Sarah trying to exit through a door labelled 'EARLY EXIT' but the door is bolted shut with chains. A sign reads 'Expensive & Complicated'. Sarah's expression is frustrated.",
    "3.38": "A final bill landing in a letterbox with a thud. The bill itemises: 'Mileage overage £450', 'Condition charges £300', 'Admin fee £75'. Bold totals in red hand-drawn marker.",
    "3.39": "Split-screen with 'PCP' on the left and 'Buy' on the right. Both sides have pros and cons being written out in marker. A balanced scale between them. Neither side is fully dominant.",
    "3.40": "A warranty certificate with an expiry stamp reading 'Year 3 — EXPIRED'. Below it, a list of car parts: brakes, tyres, timing belt. Each with a price tag. Bold 'ON YOU' written in red marker.",
    "3.41": "A monkey in mechanic overalls holding a spanner, looking at an open car bonnet. A long list of repairs on a clipboard. Monkey's expression is resigned but focused. '£1,500' written in bold red marker on the repair bill.",
    "3.42": "Two yearly maintenance scenarios side by side: Year A — 'Service + Wipers = £200' (green tick). Year B — '£1,500 repair' (red warning). Bold '£800–£1,200/year average' written in marker at the bottom.",
    "3.43": "David's car with a depreciation graph below showing value dropping from '£28,000' to '£18,000' to '£11,000' over 5 years. Each value written in bold hand-drawn marker. The curve flattens noticeably after year 3.",
    "3.44": "A graph showing steep depreciation early, then flattening after year 3. Bold annotation 'Depreciation Slows Here' with an arrow pointing at the curve's inflection point. Years labelled on the x-axis.",
    "3.45": "Same depreciation graph as above but zoomed in on years 3–10, showing the gentle flat slope. Bold text 'Time Is The Buyer's Best Friend' written in blue marker across the canvas.",
    "3.46": "A monkey with a calendar showing 10 years. PCP cycle blocks labelled 'Cycle 1', 'Cycle 2', 'Cycle 3', 'Cycle 4' fill Sarah's row. David's row shows a single loan block then 'FREE'. Monkey points at the comparison.",
    "3.47": "Sarah's 10-year receipts stacked up. Each cycle: '£16,000–£17,000' written on individual receipt stacks. A running total counter climbing in bold red marker.",
    "3.48": "A large receipt for Sarah totalling '£55,000–£65,000' in bold red hand-drawn marker. Items listed: 'Deposits', 'Payments', 'Condition Charges', 'Mileage', 'GAP'. Each line in smaller marker text.",
    "3.49": "A monkey looking at Sarah's empty driveway at Year 10. A small speech bubble: 'No car.' Sarah stands beside the monkey with hands open. Bold red 'ZERO OWNERSHIP' written on the canvas.",
    "3.50": "David's 10-year tally: '£33,060 loan + £10,000 maintenance = ~£43,000–£47,000' written in bold blue hand-drawn marker across the canvas. A simple addition illustration.",
    "3.51": "A monkey pointing proudly at David's car on his driveway. Car has '£4,000–£6,000' price tag on windscreen. A bold green 'FULLY PAID' stamp on the car. Monkey holds a thumbs-up.",
    "3.52": "Final comparison: 'David: Spent less + Has asset' written in bold green. 'Sarah: Spent more + Has nothing' written in bold red. Split-screen with dashed line between them.",
    "3.53": "A gap illustration: two parallel bars with a '£15,000–£20,000' gap highlighted in bold red between them. David's bar lower, Sarah's bar higher. '10 Years' label at the bottom. Numbers in hand-drawn marker.",
    "3.54": "A monkey standing on a timeline stretching across the canvas. Multiple car icons above it: 3, 4, 5 cars over a lifetime. Growing wealth gap illustrated with diverging lines. '× Lifetime' written in bold.",
    "3.55": "A balanced scale illustration: PCP on one side, Buy on the other. 'Sometimes PCP wins' written in neutral hand-drawn text above it. Neither side fully tipped.",
    "3.56": "A person at a desk labelled 'Accountant' with a calculator and a car on a business expense claim form. Bold text 'Business Use?' written in blue marker. A tick next to 'PCP' in that scenario only.",
    "3.57": "A monkey reading a thick car service manual for a luxury BMW. The repair bill next to it shows a large number. Bold text 'Luxury Car = Different Maths' written in marker. Monkey looks contemplative.",
    "3.58": "Two cars side by side: a BMW on the left with a 'PCP' label and a complex repair bill icon. A Ford Puma on the right with a 'Buy' label and a simpler bill. Bold 'Not The Same' written between them.",
    "3.59": "A piggy bank with '£126/month' being deposited into it. Next to it, an ISA graph growing at '8–10% annually'. Bold '£126' written in blue marker. A dotted line showing the investment trajectory.",
    "3.60": "A fork-in-the-road illustration: left path 'Invest it' leads to a growing bar chart. Right path 'Spend it' leads to a receipt pile. Bold text 'Be Honest With Yourself' written above the fork.",
    "3.61": "David driving a well-worn but paid-off Ford Puma. A 'PAID OFF' bumper sticker on the car. Calm expression. Simple background with a bold text: 'The maths doesn't care about exciting.' in hand-drawn marker.",
    "3.62": "A monkey holding a large maths textbook open to a page showing the 10-year comparison. Monkey points at the numbers with a pointer. Bold underline beneath the final totals. Monkey's expression is satisfied and knowing.",

    "4.1": "Sarah and David both walking into the dealership entrance together. Neither looks certain. Bold text 'Smart Play?' written with a question mark above the entrance.",
    "4.2": "Split-screen: Sarah with thought bubble 'Saving money'. David with thought bubble 'Building equity'. A large question mark hovers over both.",
    "4.3": "A monkey sitting at a desk staring at a very short spreadsheet showing only Month 1. A spotlight on Month 1. Everything beyond it is in shadow. Bold text 'Past Month One?' written in red marker.",
    "4.4": "A large '£28,000' price tag on a car. Below it, a tiny '£375/month' sticker. A magnifying glass circling the small sticker with an arrow labelled 'This is all they show you'. Bold numbers in marker.",
    "4.5": "A monkey at a whiteboard with a large '3 Things To Do' heading written in blue marker. Three numbered blank lines below it. Monkey holds a pen ready to write.",
    "4.6": "A large sum written in bold marker: 'Deposit + All Payments + Balloon = REAL TOTAL'. Bold red circle around 'REAL TOTAL'. A calculator beside it.",
    "4.7": "Two loan comparison forms side by side: PCP on the left, personal loan on the right. Both showing totals. Bold hand-drawn arrows comparing the full cost columns, not just the monthly.",
    "4.8": "A 2–3 year old used car with a 'SOLD: £18,000' sticker. Next to it a new car with '£28,000'. A bold green tick over the used car and red cross over the new one from a cost perspective. 'Let Someone Else Take The Hit' written in marker.",
    "4.9": "A person handing over cash for a used car. A bold 'OWNED FROM DAY ONE' banner above the scene. Simple, triumphant illustration.",

    "5.1": "A large contract document with '£28,000' at the top, labelled 'One of the biggest decisions'. A spotlight illuminating it. Around it, hidden charges illustrated as shadows.",
    "5.2": "A monkey at a chalkboard with bold text: 'No suits. No jargon. Just your money explained.' Monkey holds a piece of chalk mid-write. A subscribe button icon drawn in the corner. Monkey mid-action, chalk in hand.",
    "5.3": "A calendar showing 'New Video Every Week'. Bold circular icons of various financial topics arranged around the calendar — ISAs, mortgages, pensions, cars.",
    "5.4": "A monkey waving goodbye with one hand and holding a '£thousands saved' sign with the other. Confetti and stars around the monkey. Bold, celebratory illustration. Final scene energy.",
}

# --- MEDIA PROMPTS ---

media_scenes = {
    "0.1": "Whiteboard animation, clean white background. Monkey character present, mid-signing pose with pen in hand. Left side of frame draws in: Sarah and a PCP contract form, Ford Puma outline appears first, then contract slides in, then monkey presses pen to paper. Right side draws simultaneously: David and personal loan form. Monkey's expression: eager and focused. Camera holds steady. No mouth movement.",
    "0.2": "Whiteboard animation, clean white background. No monkey. Split-screen draws in: Sarah on left appears first with confident smile, thought bubble with thumbs-up draws in. David on right appears with nod, thought bubble with thumbs-up draws in. Large question mark fades in above both thought bubbles last. Camera pans right slowly. No mouth movement.",
    "0.3": "Whiteboard animation, clean white background. Monkey present, holding magnifying glass. Spreadsheet draws in stroke by stroke, left column first then right column. Monkey leans in with magnifying glass. Bold '£' symbol draws first, then digits '2', '8', ',', '0', '0', '0' in red marker strokes. Red arrow draws in to highlight gap. Camera zooms in slowly. No mouth movement.",
    "0.4": "Whiteboard animation, clean white background. No monkey. Ford Puma outline draws in from left to right, then filled with colour. '£28,000' writes itself in bold red marker — pound sign first, then digits. Sarah silhouette draws in on left, David on right. Dashed vertical line draws down between them. Camera holds steady. No mouth movement.",
    "0.5": "Whiteboard animation, clean white background. No monkey. Sarah draws in first on left side. PCP contract form slides in. '£2,800' writes in bold blue — pound sign, digits. 'deposit' appears below. Then '£375' writes in red — pound sign, digits — '/month' appears. Calendar with '36 months' draws in bottom right. Camera pans left slightly. No mouth movement.",
    "0.6": "Whiteboard animation, clean white background. No monkey. Dealership desk draws in first. Finance manager slides in from right, contract slides across desk toward Sarah. Stars and sparkles draw around 'full warranty' text. Speech bubble with 'Great deal!' pops in last. Camera zooms in on the sliding contract. No mouth movement.",
    "0.7": "Whiteboard animation, clean white background. No monkey. Ribbon-wrapped contract draws in, bow ties itself. 'Simple. Clean.' writes in. Scissors draw in hovering above. Shadow underneath the ribbon draws in last — subtle, ominous. Camera holds steady. No mouth movement.",
    "0.8": "Whiteboard animation, clean white background. No monkey. David draws in on right. Loan agreement document slides in beside him. '£3,000' writes stroke by stroke in blue marker, 'deposit' underneath. '£25,000' writes in blue. '7.5% APR' writes in black. '£501/month' writes in bold red — pound sign, digits, '/month'. Red circle draws around £501. '+£126 more' writes in smaller red text below. Camera zooms out slightly. No mouth movement.",
    "0.9": "Whiteboard animation, clean white background. No monkey. David's face draws in close, slightly large in frame. Thought bubble draws in, divides into two sides. '£375' writes on left in blue. '£501' writes on right in red. Arrow draws in between them pointing at the gap, '+£126' writes in red. David's eyebrow raises. Camera holds steady. No mouth movement.",
    "0.10": "Whiteboard animation, clean white background. No monkey. Forecourt draws in as background. Ford Puma draws in, then Sarah slides into driver seat. 'Day 1' banner draws in above. Sunshine rays draw out from car. David draws in on pavement, arms fold. Camera pans left following the car pulling away. No mouth movement.",
    "0.11": "Whiteboard animation, clean white background. Monkey present, holding pointer stick. Two diagrams draw in simultaneously: left — PCP loop (circular arrow with 'Pay, Return, Repeat'), right — personal loan straight line with flag. Monkey taps the finish line with pointer. Expression: curious, enlightened. Camera zooms in on the two diagrams. No mouth movement.",
    "0.12": "Whiteboard animation, clean white background. No monkey. Split-screen divides the canvas with a dashed line drawing down. Left side: Sarah draws in, coins float away, 'Renting' writes in red. Right side: David draws in, coins stack up, 'Buying' writes in green. Camera pans right. No mouth movement.",
    "0.13": "Whiteboard animation, clean white background. No monkey. Large clock draws in, hands sweep forward. Two bar charts draw upward simultaneously — David's grows taller, Sarah's stays flat. '£thousands' writes on y-axis. Arrow draws in pointing at gap between bars. Camera zooms out to show full comparison. No mouth movement.",

    "1.1": "Whiteboard animation, clean white background. Monkey present, inside car interior sketch. Car interior draws in first — steering wheel, seats, mirror. Air freshener draws in swinging. 'NEW CAR SMELL' writes in swirly letters in speech bubble. Monkey's hand grips wheel, expression: blissful, eyes half-closed contentedly. Camera holds steady. No mouth movement.",
    "1.2": "Whiteboard animation, clean white background. No monkey. Three comic panels draw in left to right. Panel 1: engine with crossed spanner draws, then 'COVERED' stamp slams down in green. Panel 2: brake pads draw, then 'COVERED' stamp. Panel 3: AC unit draws, then 'COVERED' stamp. Camera pans right across panels. No mouth movement.",
    "1.3": "Whiteboard animation, clean white background. No monkey. Row of bill envelopes draws in. Each gets 'VOID' stamp one by one. Sarah draws in walking past them, hands in pockets, smiling. Camera holds steady. No mouth movement.",
    "1.4": "Whiteboard animation, clean white background. No monkey. David draws in on left. Car draws in on right with value arrow pointing down. Depreciation graph draws in beneath the car. '£501' writes in bold red — pound sign, digits, '/month'. David's expression: grimly determined. Camera pans left. No mouth movement.",
    "1.5": "Whiteboard animation, clean white background. No monkey. Ford Puma draws in centre. Three price tags pop in sequentially: '£28,000' first in black — pound sign then digits, '£24,000' draws in red at Day 1 label, '£21,000' draws in red at Year 1 label. Bold red downward arrows draw between each tag. Labels 'Day 1', 'Year 1' write in. Camera zooms in on the price tags. No mouth movement.",
    "1.6": "Whiteboard animation, clean white background. No monkey. Two parallel bars draw upward: 'Car Value' bar on left draws in blue, reaching '£18,000' — digits write on bar. 'Loan Balance' bar on right draws in red, taller, reaching '£20,000' — digits write on bar. Gap highlighted with bracket. Camera holds steady, emphasis zoom on the gap. No mouth movement.",
    "1.7": "Whiteboard animation, clean white background. Monkey present at edge of hole. Hole draws in first. David's silhouette appears below. Monkey draws in peering down, holding rope. 'UNDERWATER' writes at bottom of hole. '£2,000 underwater' writes in red marker — pound sign, digits, 'underwater' — beside hole. Monkey's expression: alarmed. Camera zooms in on hole. No mouth movement.",
    "1.8": "Whiteboard animation, clean white background. No monkey. Street scene draws in. Sarah draws in on left, arms fold, smug expression forms. Thought bubble: 'I made the right call.' draws in. David draws in background next to car, stoic. Camera pans right to show both characters. No mouth movement.",

    "2.1": "Whiteboard animation, clean white background. Monkey present with calculator and pen. Large canvas draws in. Left column header 'Sarah' writes in blue. '£2,800' writes — pound sign, digits — then '+' then '36 ×' then '£375' writes — pound sign, digits. '=' draws, then '£16,300' writes in bold blue. Monkey writes each element with pen, expression: focused, concentrated. Camera holds steady. No mouth movement.",
    "2.2": "Whiteboard animation, clean white background. Monkey still present from previous scene. Right column header 'David' writes in red. '£3,000' writes — pound sign, digits — then '+' then '36 ×' then '£501' writes — pound sign, digits. '=' draws, then '£21,036' writes in bold red. Double underline draws beneath both totals. Camera pans right. No mouth movement.",
    "2.3": "Whiteboard animation, clean white background. No monkey. Scoreboard draws in — header first, then Sarah's column '£16,300' in blue writes in, then David's column '£21,036' in red writes in. Arrow draws pointing at Sarah's lower number. 'Winning?' writes beside it. Large question mark draws in above the board last. '£5,000' writes with a bracket showing the gap. Camera zooms out. No mouth movement.",

    "3.1": "Whiteboard animation, clean white background. No monkey. Road draws in leading to dealership. Sarah and car draw in approaching. Signpost draws in with three arrows — each arrow draws in and label writes sequentially: '1. Pay Balloon', '2. Hand Keys Back', '3. New PCP'. Sarah's hand moves to chin. Camera pans right toward the signpost. No mouth movement.",
    "3.2": "Whiteboard animation, clean white background. No monkey. Large canvas area fills with bold text: '£12,000' writes large in red — pound sign, then '1', '2', ',', '0', '0', '0' — 'Balloon Payment' writes below. Receipt draws in with total '£28,300' — pound sign, digits. Shocked-face icon draws beside it. Camera zooms in on the £12,000 figure. No mouth movement.",
    "3.3": "Whiteboard animation, clean white background. No monkey. Counter draws in. Sarah draws in offering keys to manager. Keys lift and cross the counter. Receipt pile draws in behind Sarah labelled '£16,300'. Large red 'X' draws over the pile, 'Gone' writes in red. Sarah's shoulders drop. Camera holds steady. No mouth movement.",
    "3.4": "Whiteboard animation, clean white background. Monkey present on conveyor belt. Belt draws in moving right. Step labels write in one by one: 'New Deal', 'Payments', 'Return', 'New Deal', 'Payments'. Monkey draws in walking on belt. Circular 'Repeat' arrow draws above. Monkey's expression: dizzy but resigned. Camera pans right following the belt. No mouth movement.",
    "3.5": "Whiteboard animation, clean white background. No monkey. New car draws in. Odometer draws in showing '0' resetting — digits spin back to zero. Payment counter draws beside it showing '£375/month' still ticking. Two arrows draw: one pointing left 'Reset', one pointing right 'Still Running'. Camera holds steady. No mouth movement.",
    "3.6": "Whiteboard animation, clean white background. No monkey. Calendar draws in. Marker circles Month 36 in green — circle draws around the date. David draws in pointing at calendar. Loan balance meter draws in: bar fills from right to left leaving '24 payments' remaining. Bold '24' writes in blue marker — '2' then '4' — then circle draws around it. Camera pans left. No mouth movement.",
    "3.7": "Whiteboard animation, clean white background. No monkey. Path draws in as stepping stones left to right. David draws in on path. Payment numbers write in on each stone: '37', '38', '39'... trailing off. Flag at far right draws in, 'OWNED' writes on it. Arrow draws pointing toward flag. Camera pans right following the path. No mouth movement.",
    "3.8": "Whiteboard animation, clean white background. No monkey. Dashed vertical line draws down splitting frame. Left side: Sarah's path draws, leads to revolving door drawing in, 'Start Over' writes on it. Right side: David's path draws, leads to finish-line flag drawing in, 'Done' writes. Camera holds steady, pulls back slightly to show full split. No mouth movement.",
    "3.9": "Whiteboard animation, clean white background. Monkey present holding two signs. Left sign draws in: circular PCP loop draws — arrows going round and round. Right sign draws in: straight line draws with flag at end. Monkey's expression: wide-eyed, pointing between them. Pointer draws from monkey's hand toward the finish line. Camera zooms in on the two signs. No mouth movement.",
    "3.10": "Whiteboard animation, clean white background. No monkey. Large calendar draws in. Month 60 date highlighted — green circle draws around it. David draws in beside calendar, arm raises in celebration. Confetti bursts appear. Loan document draws in, 'PAID IN FULL' stamp slams down over it. Camera zooms in on the stamp. No mouth movement.",
    "3.11": "Whiteboard animation, clean white background. No monkey. Driveway draws in with car on it. Three small icons draw in below car sequentially: insurance shield, fuel pump, spanner. Simple connecting line draws between them. 'That's it.' writes in bold beside the icons. Camera pans left slowly. No mouth movement.",
    "3.12": "Whiteboard animation, clean white background. No monkey. Simple cost chart draws in — bars first, then labels write in: 'Insurance', 'Fuel', 'Maintenance'. Sum writes in: '= £70–£100/month' — digits write stroke by stroke in bold green marker. Green tick draws beside the total. Camera holds steady. No mouth movement.",
    "3.13": "Whiteboard animation, clean white background. No monkey. Sarah draws in sitting in car interior. Phone notification pops into frame: '£375 payment due' writes on screen. Calendar Month 61 draws in background. Sarah's expression: neutral, habituated. Camera zooms in on the phone notification. No mouth movement.",
    "3.14": "Whiteboard animation, clean white background. Monkey present reading newspaper. Newspaper draws in first. Headline writes across it: 'MONTHLY PAYMENT IS JUST NORMAL NOW'. Coffee mug draws in monkey's other hand. Red warning sign draws in corner last — triangle draws, then 'DANGER' writes inside. Monkey's expression: blissfully unaware. Camera pans right toward warning sign. No mouth movement.",
    "3.15": "Whiteboard animation, clean white background. No monkey. Scoreboard frame draws in with header 'End of Year 6'. Two columns draw in: 'Sarah' header writes in red, 'David' header writes in blue. 'VS' writes in black between columns. Blank lines below ready for numbers. Camera zooms out to frame full scoreboard. No mouth movement.",
    "3.16": "Whiteboard animation, clean white background. No monkey. Receipt 1 draws in: '£2,800' writes — pound sign, digits — then '+' then '£13,500' writes — digits — then '= £16,300' writes. Receipt 2 draws in below it mirroring same. Grand total '£32,600' writes in bold red large marker — pound sign, '3', '2', ',', '6', '0', '0'. Camera holds steady. No mouth movement.",
    "3.17": "Whiteboard animation, clean white background. No monkey. Sarah draws in centre frame, hands open, shocked expression. Receipt pile draws in behind her. Empty driveway draws in front of her. 'Zero Assets' writes in bold red — each word appears with emphasis. Camera zooms out to show the emptiness around her. No mouth movement.",
    "3.18": "Whiteboard animation, clean white background. No monkey. Large receipt draws in. Line items write in sequence: '£3,000' — pound sign, digits — then '+' then '£30,060' — pound sign, digits — then '= £33,060' writes in bold blue large text — pound sign, '3', '3', ',', '0', '6', '0'. Double underline draws beneath. Camera pans right. No mouth movement.",
    "3.19": "Whiteboard animation, clean white background. No monkey. David draws in standing beside car. 'OWNED' badge draws onto car and fills with colour. Price tags write on windscreen: '£9,000–£11,000' — digits write in. Monthly payment counter draws below showing '£0/month' — '£0' writes in bold green — pound sign, zero. Camera zooms in on the owned badge. No mouth movement.",
    "3.20": "Whiteboard animation, clean white background. No monkey. Large maths equation draws in stroke by stroke: '£33,060' writes in red, '−' draws, '£10,000' writes in green (asset value), '≈' draws, '£23,000' writes in bold blue. Bracket draws under the asset figure labelled 'car value'. Camera holds steady, emphasis on the result. No mouth movement.",
    "3.21": "Whiteboard animation, clean white background. No monkey. Sarah's column draws in on left. '£32,600 spent' writes large in red — pound sign then digits. Below it 'Assets: £0' writes in red. Bold underline draws beneath both lines. Camera zooms in on the zero. No mouth movement.",
    "3.22": "Whiteboard animation, clean white background. Monkey present pointing at scoreboard. Scoreboard draws in. Sarah's column writes: '£32,600' in red then '/ Zero' in red. David's column writes: '~£23,000' in blue then '/ Car: £10k' in blue. Monkey draws in beside board, arm extends with pointer. Red circle draws around asset column. Monkey's expression: wide-eyed, amazed. Camera pans left toward monkey. No mouth movement.",
    "3.23": "Whiteboard animation, clean white background. No monkey. Seesaw/balance beam draws in from centre outward. Left end (Sarah) weighs down — receipts pile draws in and the beam tilts left. Right end (David) rises — car icon draws in. Bold 'THE FLIP' writes above the seesaw in red arc. Camera zooms out to show full balance. No mouth movement.",
    "3.24": "Whiteboard animation, clean white background. No monkey. Desk draws in. Finance manager's hand draws in. Small card slides across desk — '£375' writes on it in bold red — pound sign, '3', '7', '5'. Black curtain draws in covering rest of desk, 'CONDITIONS' label writes on curtain. Camera zooms in on the sliding card. No mouth movement.",
    "3.25": "Whiteboard animation, clean white background. No monkey. Advertisement banner draws in. '£375/month' writes in giant bold text — pound sign, digits. Tiny font text draws below. Red circle draws around tiny text. Arrow draws from circle with question mark at end. Camera zooms in on the tiny text. No mouth movement.",
    "3.26": "Whiteboard animation, clean white background. Monkey present unrolling scroll. Scroll draws out from monkey's hands getting longer. Items write sequentially: 'Mileage Cap', 'Condition Charges', 'GAP Insurance', 'Early Exit Fees'. Monkey's expression: increasingly surprised as scroll grows. Camera pans right following scroll unfurling. No mouth movement.",
    "3.27": "Whiteboard animation, clean white background. No monkey. Speedometer draws in. Needle swings to cap line — '10,000 miles/year' writes at cap in red. Needle pushes past cap — 'OVER' writes in red with arrow. Below: '8' writes, '–' draws, '15p per mile' writes stroke by stroke in bold red marker. Camera holds steady, emphasis zoom on the 'OVER' area. No mouth movement.",
    "3.28": "Whiteboard animation, clean white background. No monkey. Bold text draws in sequentially: '8' writes, '–' draws, '15p per mile' writes in red. Below: '3,000 miles over' writes, '=' draws, 'up to £450' writes in bold red — pound sign, '4', '5', '0'. Surprise billing envelope draws in right side, shocked face pops out of it. Camera pans left. No mouth movement.",
    "3.29": "Whiteboard animation, clean white background. Monkey present receiving envelope. Dealership counter draws in. Envelope draws in with 'SURPRISE' label. '£450' writes on envelope in bold red — pound sign, '4', '5', '0'. Monkey draws in, arm extends to receive envelope, holds it at arm's length. Monkey's expression: horrified, eyes wide. Camera zooms in on monkey's face. No mouth movement.",
    "3.30": "Whiteboard animation, clean white background. No monkey. Car bumper draws in. Scuff mark draws as small irregular shape. Red circle draws around it. Magnifying glass draws in over scuff. Dealer with clipboard draws in behind the car, pencil moves to clipboard. Shadow draws over scene. Camera zooms in on the scuff. No mouth movement.",
    "3.31": "Whiteboard animation, clean white background. No monkey. Three damage illustrations draw in sequentially: bumper scuff draws, red circle draws around it, price tag '£250+' writes and hangs from circle. Interior mark draws, circle and tag appear. Cracked alloy draws, circle and 'CHARGEABLE' stamp slams down. Camera pans right across the three items. No mouth movement.",
    "3.32": "Whiteboard animation, clean white background. Monkey present at desk. Desk and two chairs draw in. Finance manager draws in on opposite side. GAP insurance brochure slides across desk. '£350' writes on brochure in bold red — pound sign, '3', '5', '0'. Monkey draws in, leans back sceptically, one eyebrow raised. Monkey's expression: suspicious, arms crossed. Camera holds steady. No mouth movement.",
    "3.33": "Whiteboard animation, clean white background. No monkey. Totalled car draws in on left, tow truck hooks on. Insurance cheque draws in on right — cheque writes in with amount. Finance outstanding figure draws above cheque. Gap between the two amounts highlights in red, 'THE GAP' writes in red with bracket. Camera pans right. No mouth movement.",
    "3.34": "Whiteboard animation, clean white background. No monkey. Credit card draws in large, front face. 'Section 75 CCA' writes on card face. Protective shield draws around card, glows green. 'Already Protected?' writes in bold blue above the card with question mark. Camera zooms in on the shield. No mouth movement.",
    "3.35": "Whiteboard animation, clean white background. Monkey present holding two price tags. Dealer price tag draws in monkey's left hand: '£350 GAP' writes in red — pound sign, '3', '5', '0'. Independent price tag draws in monkey's right hand: '£80 GAP' writes in green — pound sign, '8', '0'. Monkey's right arm extends, thumb draws up beside cheaper tag. Monkey's expression: pleased, decisive. Camera pans right. No mouth movement.",
    "3.36": "Whiteboard animation, clean white background. No monkey. PCP contract draws in with padlock icon stamping onto it. Life-change icons draw in around the contract: moving box, baby pram, briefcase with 'REDUNDANT' stamp writes on it. Arrows draw from each icon pointing toward the locked contract. Camera zooms out to show all icons surrounding it. No mouth movement.",
    "3.37": "Whiteboard animation, clean white background. No monkey. Door labelled 'EARLY EXIT' draws in. Chains and bolt draw across door. Sarah draws in pushing against door, not moving. Sign writes on door: 'Expensive & Complicated'. Sarah's hand pushes, frustration in posture. Camera holds steady. No mouth movement.",
    "3.38": "Whiteboard animation, clean white background. No monkey. Letterbox draws in. Bill envelope flies in and drops into letterbox with impact lines. Bill unfolds showing three line items writing in sequentially: 'Mileage overage £450' writes — pound sign, digits — 'Condition charges £300' writes, 'Admin fee £75' writes. Total underlines itself. Camera zooms in on the bill. No mouth movement.",
    "3.39": "Whiteboard animation, clean white background. No monkey. Canvas splits with dashed line drawing down. Left: 'PCP' header writes, pros and cons list starts writing in. Right: 'Buy' header writes, pros and cons list writes. Balanced scale draws in centre between panels. Camera holds steady showing both sides. No mouth movement.",
    "3.40": "Whiteboard animation, clean white background. No monkey. Warranty certificate draws in. Stamp draws on it: 'Year 3 — EXPIRED' writes in red ink. Below: list draws in — 'Brakes', 'Tyres', 'Timing Belt' write sequentially, each with a price tag drawing in. 'ON YOU' writes in bold red across the list. Camera pans left. No mouth movement.",
    "3.41": "Whiteboard animation, clean white background. Monkey present in mechanic overalls. Car bonnet draws open. Monkey draws in beside bonnet with spanner. Clipboard draws in monkey's other hand, repair list writes onto it. '£1,500' writes on repair bill drawing in to the right — pound sign, '1', ',', '5', '0', '0' — in bold red. Monkey's expression: resigned, focused. Camera zooms in on repair bill. No mouth movement.",
    "3.42": "Whiteboard animation, clean white background. No monkey. Two scenario panels draw in side by side. Year A panel: 'Service + Wipers' writes, '= £200' writes in green. Year B panel: '£1,500 repair' writes in red — pound sign, digits. Below both panels: '£800–£1,200/year average' writes in marker. Green tick and red warning draw beside respective panels. Camera holds steady. No mouth movement.",
    "3.43": "Whiteboard animation, clean white background. No monkey. Ford Puma draws in. Depreciation graph draws beneath it — x-axis (years 0–5) draws, y-axis (value) draws. Curve plots from left: '£28,000' writes at year 0 — pound sign, digits — curve dips, '£18,000' writes at year 2, curve continues to '£11,000' at year 5. Camera pans right following the curve. No mouth movement.",
    "3.44": "Whiteboard animation, clean white background. No monkey. Same depreciation curve but zoomed in — curve draws in flattening after year 3. Arrow draws pointing at inflection point. 'Depreciation Slows Here' writes beside arrow. Years label on x-axis write in. Camera zooms in on the inflection point. No mouth movement.",
    "3.45": "Whiteboard animation, clean white background. No monkey. Flat portion of depreciation curve draws in large. 'Time Is The Buyer's Best Friend' writes in bold blue marker across canvas — each word draws in sequentially. Underline sweeps beneath the text. Camera holds steady, emphasis on the text. No mouth movement.",
    "3.46": "Whiteboard animation, clean white background. Monkey present with calendar. Calendar draws in showing 10-year span. Sarah's row fills in from left: 'Cycle 1' block draws, 'Cycle 2' draws, 'Cycle 3' draws, 'Cycle 4' draws in red. David's row: single loan block draws in blue, then 'FREE' writes in green for remaining years. Monkey draws in pointing at comparison. Monkey's expression: enlightened, pointing with emphasis. Camera zooms out. No mouth movement.",
    "3.47": "Whiteboard animation, clean white background. No monkey. Receipt stacks draw in one by one. Each stack: '£16,000–£17,000' writes on it in red. Running total counter draws below, digits incrementing: '£16k', '£32k', '£48k', '£64k'. Bold red numbers write at each increment. Camera pans right following the stacking. No mouth movement.",
    "3.48": "Whiteboard animation, clean white background. No monkey. Large receipt draws in. Items write sequentially from top: 'Deposits' writes with amount, 'Payments' writes with amount, 'Condition Charges' writes, 'Mileage' writes, 'GAP' writes. Total line draws at bottom: '£55,000–£65,000' writes in bold red — pound sign, '5', '5', ',', '0', '0', '0' — '–' draws, '£65,000' writes. Camera zooms out to show full receipt. No mouth movement.",
    "3.49": "Whiteboard animation, clean white background. Monkey present at empty driveway. Driveway draws in. Empty space where car should be draws with dotted outline. Sarah draws in beside monkey, hands open. Monkey looks at empty space. 'ZERO OWNERSHIP' writes in bold red — each word appears with emphasis. Monkey's expression: sad, sympathetic. Camera pans left. No mouth movement.",
    "3.50": "Whiteboard animation, clean white background. No monkey. Large addition draws in: '£33,060' writes in blue — pound sign, digits — then '+' draws, '£10,000' writes in orange (maintenance) — pound sign, digits — '≈' draws, '£43,000–£47,000' writes in bold blue — pound sign, digits — '–' draws, digits. Bracket under maintenance amount labels 'maintenance'. Camera holds steady. No mouth movement.",
    "3.51": "Whiteboard animation, clean white background. Monkey present pointing at car. David's driveway draws in. Car draws on driveway. 'FULLY PAID' stamp slams onto car windscreen. Price tag draws on windscreen: '£4,000–£6,000' writes — pound sign, digits. Monkey draws in beside car, arm extends pointing, thumb up on other hand. Monkey's expression: proud, beaming. Camera zooms in on the stamp. No mouth movement.",
    "3.52": "Whiteboard animation, clean white background. No monkey. Dashed line draws down splitting canvas. Left side: 'Sarah' header writes, 'Spent More' writes in red, '+ Has Nothing' writes in red. Right side: 'David' header writes, 'Spent Less' writes in green, '+ Has Asset' writes in green. Camera holds steady. No mouth movement.",
    "3.53": "Whiteboard animation, clean white background. No monkey. Two parallel horizontal bars draw in — David's bar first (shorter, blue), Sarah's bar second (taller, red). Gap between them highlights: bracket draws, '£15,000–£20,000' writes in bold red — pound sign, '1', '5', ',', '0', '0', '0'. '10 Years' label writes below. Camera zooms in on the gap bracket. No mouth movement.",
    "3.54": "Whiteboard animation, clean white background. Monkey present on timeline. Long timeline draws left to right. Car icons draw above timeline at intervals — 3 then 4 then 5 icons. Two diverging lines draw: top line labelled 'PCP path' curves upward in red, bottom line labelled 'Buy path' stays lower in blue. '× Lifetime' writes at far right. Monkey stands at start of timeline, expression: knowing, contemplative. Camera pans right following timeline. No mouth movement.",
    "3.55": "Whiteboard animation, clean white background. No monkey. Balance scale draws in from centre outward. 'PCP' writes on left pan, 'Buy' writes on right pan. Scale sits level. 'Sometimes PCP wins' writes in neutral black above scale. Question mark draws above scale. Camera holds steady. No mouth movement.",
    "3.56": "Whiteboard animation, clean white background. No monkey. Office desk draws in. Accountant figure draws in behind desk. Calculator draws, car expense claim form draws with pen writing on it. 'Business Use?' writes in bold blue above the scene. Green tick draws beside 'PCP' on the form. Camera pans right. No mouth movement.",
    "3.57": "Whiteboard animation, clean white background. Monkey present reading manual. Thick car service manual draws in, monkey draws in holding it open. Repair bill draws to monkey's right — large number writes on bill. 'Luxury Car = Different Maths' writes in bold blue above the scene. Monkey's expression: contemplative, thoughtful. Camera zooms in on the repair bill. No mouth movement.",
    "3.58": "Whiteboard animation, clean white background. No monkey. Dashed line draws splitting canvas. Left: BMW silhouette draws, 'PCP' writes above it, complex repair bill icon draws beside it. Right: Ford Puma draws, 'Buy' writes above it, simpler bill icon draws. 'Not The Same' writes in bold between the two cars. Camera holds steady. No mouth movement.",
    "3.59": "Whiteboard animation, clean white background. No monkey. Piggy bank draws in on left. '£126/month' writes above it in blue — pound sign, '1', '2', '6', '/month'. Coin draws and drops into piggy bank. ISA growth graph draws on right — bars grow upward, '8–10% annually' writes in green. Dotted line draws connecting piggy bank to growing graph. Camera pans right. No mouth movement.",
    "3.60": "Whiteboard animation, clean white background. No monkey. Fork-in-road illustration draws from bottom. Left path draws: 'Invest it' writes, leads to growing bar chart drawing in at path's end. Right path draws: 'Spend it' writes, leads to receipt pile drawing in at path's end. 'Be Honest With Yourself' writes in bold above the fork. Camera zooms out to show full fork. No mouth movement.",
    "3.61": "Whiteboard animation, clean white background. No monkey. David draws in driving a worn but well-maintained car. 'PAID OFF' bumper sticker draws onto rear bumper. David's expression: calm, content. 'The maths doesn't care about exciting.' writes across the canvas in bold hand-drawn style — each word writes sequentially. Camera holds steady. No mouth movement.",
    "3.62": "Whiteboard animation, clean white background. Monkey present holding open textbook. Large open maths textbook draws in. Page shows 10-year comparison table drawing in — Sarah column in red, David column in blue. Monkey draws in holding book open, pointer draws and indicates final row totals. Monkey's expression: satisfied, knowing. Camera zooms in on the comparison table. No mouth movement.",

    "4.1": "Whiteboard animation, clean white background. No monkey. Dealership entrance draws in. Sarah draws in on left, David on right, both walking toward entrance. Neither expression is certain — puzzled looks. 'Smart Play?' writes in bold above the entrance with question mark. Camera holds steady. No mouth movement.",
    "4.2": "Whiteboard animation, clean white background. No monkey. Split-screen with dashed line drawing down. Sarah draws on left: thought bubble draws, 'Saving money' writes inside in green. David draws on right: thought bubble draws, 'Building equity' writes inside in blue. Large question mark draws above both thought bubbles simultaneously. Camera zooms out. No mouth movement.",
    "4.3": "Whiteboard animation, clean white background. Monkey present at desk. Small desk draws in. Monkey draws in sitting at it. Sparse spreadsheet draws with only Month 1 visible. Spotlight effect draws around Month 1. Everything beyond it shown as shadow/blur. 'Past Month One?' writes in bold red — question mark draws last. Monkey's expression: sheepish, eye-opening realisation. Camera zooms in on Month 1. No mouth movement.",
    "4.4": "Whiteboard animation, clean white background. No monkey. Car draws in with large price tag: '£28,000' writes in bold — pound sign, digits. Below it small sticker draws: '£375/month' writes in tiny text — pound sign, digits. Magnifying glass draws circling the small sticker. Arrow draws from magnifying glass with label 'This is all they show you' writing in. Camera zooms in on the small sticker. No mouth movement.",
    "4.5": "Whiteboard animation, clean white background. Monkey present at whiteboard. Large whiteboard draws in. '3 Things To Do' header writes in bold blue — one word at a time. Three numbered blank lines draw below. Monkey draws in holding pen ready, expression: determined, focused. Camera holds steady. No mouth movement.",
    "4.6": "Whiteboard animation, clean white background. No monkey. Large sum draws in equation style: 'Deposit' writes, '+' draws, 'All Payments' writes, '+' draws, 'Balloon' writes, '=' draws, 'REAL TOTAL' writes in bold red with a circle drawing around it. Calculator draws beside the equation. Camera pans right. No mouth movement.",
    "4.7": "Whiteboard animation, clean white background. No monkey. Two forms draw in side by side: 'PCP' header writes on left form, 'Personal Loan' header writes on right form. Monthly row highlights on both, then total row highlights. Bold arrows draw comparing the total rows — not the monthly rows. 'Compare These' writes above the total rows. Camera holds steady. No mouth movement.",
    "4.8": "Whiteboard animation, clean white background. No monkey. Two cars draw in side by side: new car on right with '£28,000' price tag writing in — pound sign, digits. Two-year-old used car on left with '£18,000' writing in — pound sign, digits. Green tick draws over used car. 'Let Someone Else Take The Hit' writes in bold below in marker. Camera pans left toward used car. No mouth movement.",
    "4.9": "Whiteboard animation, clean white background. No monkey. Person draws in handing cash over. Used car draws with keys transferring. 'OWNED FROM DAY ONE' banner draws in above — letters appear one by one. Celebratory stars and check mark draw around the scene. Camera zooms out. No mouth movement.",

    "5.1": "Whiteboard animation, clean white background. No monkey. Large contract document draws in — '£28,000' writes at top in bold — pound sign, digits. Spotlight draws illuminating the contract. Shadow shapes draw around the edges representing hidden charges. 'Biggest Decision?' writes in bold above. Camera zooms in on the contract. No mouth movement.",
    "5.2": "Whiteboard animation, clean white background. Monkey present at chalkboard. Chalkboard draws in. Monkey draws in with chalk in hand mid-write. Text writes stroke by stroke: 'No suits.' writes, 'No jargon.' writes, 'Just your money explained.' writes. Subscribe button icon draws in corner — circle draws, then play triangle draws inside. Monkey's expression: proud, welcoming. Camera holds steady. No mouth movement.",
    "5.3": "Whiteboard animation, clean white background. No monkey. Calendar draws in with 'New Video Every Week' writes above it. Financial topic icons draw in around the calendar sequentially: ISA badge draws, mortgage house draws, pension piggy bank draws, car draws. Connecting lines draw from each icon to calendar. Camera zooms out to show all icons. No mouth movement.",
    "5.4": "Whiteboard animation, clean white background. Monkey present waving. Monkey draws in centre. One arm raises, hand waves. Other arm raises holding sign that draws in — '£thousands saved' writes on sign in bold blue — pound sign, 'thousands saved'. Confetti bursts draw from top of frame falling. Stars draw around monkey. Monkey's expression: joyful, celebratory. Camera zooms out for wide farewell shot. No mouth movement.",
}

# Build scene order
scene_order = [
    "0.1","0.2","0.3","0.4","0.5","0.6","0.7","0.8","0.9","0.10","0.11","0.12","0.13",
    "1.1","1.2","1.3","1.4","1.5","1.6","1.7","1.8",
    "2.1","2.2","2.3",
    "3.1","3.2","3.3","3.4","3.5","3.6","3.7","3.8","3.9","3.10",
    "3.11","3.12","3.13","3.14","3.15","3.16","3.17","3.18","3.19","3.20",
    "3.21","3.22","3.23","3.24","3.25","3.26","3.27","3.28","3.29","3.30",
    "3.31","3.32","3.33","3.34","3.35","3.36","3.37","3.38","3.39","3.40",
    "3.41","3.42","3.43","3.44","3.45","3.46","3.47","3.48","3.49","3.50",
    "3.51","3.52","3.53","3.54","3.55","3.56","3.57","3.58","3.59","3.60",
    "3.61","3.62",
    "4.1","4.2","4.3","4.4","4.5","4.6","4.7","4.8","4.9",
    "5.1","5.2","5.3","5.4"
]

assert len(scene_order) == 99, f"Expected 99 scenes, got {len(scene_order)}"
assert len(image_scenes) == 99, f"Expected 99 image prompts, got {len(image_scenes)}"
assert len(media_scenes) == 99, f"Expected 99 media prompts, got {len(media_scenes)}"

# Build image prompts file content
image_lines = []
for s in scene_order:
    prompt = f"{s} {PREFIX} {image_scenes[s]} {SUFFIX}"
    image_lines.append(prompt)
    image_lines.append("")

image_content = "\n".join(image_lines).rstrip("\n")

# Build media prompts file content
media_lines = []
for s in scene_order:
    prompt = f"{s} {media_scenes[s]}"
    media_lines.append(prompt)
    media_lines.append("")

media_content = "\n".join(media_lines).rstrip("\n")

# Verify counts
image_count = sum(1 for l in image_lines if l and not l.startswith("\n"))
media_count = sum(1 for l in media_lines if l and not l.startswith("\n"))
print(f"Image prompts: {len(scene_order)} scenes confirmed")
print(f"Media prompts: {len(scene_order)} scenes confirmed")

# --- Upload to Drive ---
import json as json_mod
import requests as req

with open('/home/user/ClaudeCode/token.json') as f:
    tok = json_mod.load(f)

r = req.post('https://oauth2.googleapis.com/token', data={
    'client_id': tok['client_id'],
    'client_secret': tok['client_secret'],
    'refresh_token': tok['refresh_token'],
    'grant_type': 'refresh_token'
})
access_token = r.json()['access_token']
print("Access token obtained.")

FOLDER_ID = '1MFf07I2leM6_iyvB5bGXNyqRgYhv35SI'

def upload_file(filename, content, access_token, folder_id):
    r = req.post(
        'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
        headers={'Authorization': f'Bearer {access_token}'},
        files={
            'metadata': (None, json_mod.dumps({'name': filename, 'parents': [folder_id]}), 'application/json'),
            'file': (filename, content.encode('utf-8'), 'text/plain; charset=utf-8')
        }
    )
    return r.json()

img_result = upload_file('04-image-prompts.txt', image_content, access_token, FOLDER_ID)
print(f"04-image-prompts.txt uploaded. File ID: {img_result.get('id')}")

med_result = upload_file('05-media-prompts.txt', media_content, access_token, FOLDER_ID)
print(f"05-media-prompts.txt uploaded. File ID: {med_result.get('id')}")
