# deBunq · demo video script

Target length: **3 minutes**

Goal: show that deBunq is not just a scanner or spam filter.
It is a **scam shield inside the payment flow**.

---

## Total: 3:00

| Block                                  |      Time | Visual                                                  | Voiceover                                                                                                                                                                                                                                                                             |
| -------------------------------------- | --------: | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. Hook**                            | 0:00–0:15 | Title card → deBunq logo or inbox screen                | “We all receive payment requests in different places. An invoice by email. A PDF from insurance. A screenshot from someone. Or even a voice note asking for money urgently. Some are real. Some are scams. The problem is that once you press pay, the damage is often already done.” |
| **B. Problem**                         | 0:15–0:30 | Show fake email or suspicious message                   | “A normal spam filter only asks one question: should this message be in your inbox? deBunq asks a more important question: should this request be allowed to become a bank payment?”                                                                                                  |
| **C. Setup**                           | 0:30–0:45 | Cut to deBunq inbox screen                              | “Meet deBunq. It debunks every payment request before you pay. You can paste an email, upload a PDF, take a picture of a bill, or upload a suspicious voice note. Then deBunq gives it a TrustScore before bunq prepares any action.”                                                 |
| **D. Scenario 1 — phishing email**     | 0:45–1:20 | Paste fake phishing email → tap analyze                 | “Let’s start with a phishing email. It looks like a normal company message. But it has urgency, a suspicious link, and payment details that should make us pause.”                                                                                                                    |
|                                        |           | TrustScore appears with low score                       | “deBunq scores it low. The result is not just ‘scam’ or ‘not scam’. It explains why. The issuer looks suspicious. The urgency is high. The payment details do not feel trustworthy.”                                                                                                  |
|                                        |           | Scroll to blocked action                                | “Because the TrustScore is too low, deBunq blocks the bunq action. This is the important part. The protection is not only visual. The backend refuses the payment flow.”                                                                                                              |
| **E. Scenario 2 — voice scam**         | 1:20–1:55 | Upload voice note → tap analyze                         | “Now we test a different kind of scam. A voice note says something like: ‘Hi mom, I lost my phone. Please send money urgently. Don’t tell anyone.’ This is not a normal invoice. But it is still a payment request.”                                                                  |
|                                        |           | Transcript and low TrustScore                           | “deBunq turns the voice note into text and checks the risk. It detects family impersonation, urgency, secrecy, and missing payment context.”                                                                                                                                          |
|                                        |           | Blocked result                                          | “Again, the request is blocked before it can become a bunq payment. This is why multimodal input matters. Scams do not only arrive as emails.”                                                                                                                                        |
| **F. Scenario 3 — legitimate invoice** | 1:55–2:35 | Take photo or upload real invoice                       | “Now let’s use a real invoice. This is the convenience side of deBunq. Normally I would have to copy the amount, IBAN, beneficiary, reference, and due date by hand. That is slow and easy to get wrong.”                                                                             |
|                                        |           | Green TrustScore                                        | “Here, deBunq gives it a high TrustScore. The issuer looks consistent. The IBAN format is valid. The payment details are complete. There is no suspicious urgency.”                                                                                                                   |
|                                        |           | Show bunq pre-flight card                               | “Then deBunq prepares the bunq pre-flight. I can see the account, the beneficiary, the amount, the reference, and the scheduled date before anything happens.”                                                                                                                        |
|                                        |           | Tap confirm                                             | “I confirm the action.”                                                                                                                                                                                                                                                               |
|                                        |           | Show receipt with bunq id                               | “And now we get a bunq sandbox receipt. The payment action was created through the bunq API. The safe request goes through. The suspicious ones were blocked.”                                                                                                                        |
| **G. Stack flash**                     | 2:35–2:50 | Quick montage: backend logs, Bedrock, bunq API response | “Under the hood, the frontend is built with Next.js, React, TypeScript, and Tailwind. The backend uses FastAPI. Claude on AWS Bedrock handles document reasoning and TrustScore analysis. The bunq sandbox API creates the real payment action.”                                      |
| **H. Close**                           | 2:50–3:00 | Title card or final app screen                          | “deBunq is a scam shield inside the payment flow. It blocks the scam, and helps pay the real bill safely.”                                                                                                                                                                            |

---

## Shorter one-take voiceover version

Use this if you want to record without reading a table.

“Payment scams do not always look like scams anymore.

They can look like a real invoice. They can arrive as a PDF. They can be a screenshot. They can even be a voice note from someone pretending to need money urgently.

A normal spam filter protects the inbox. deBunq protects the payment flow.

Here is the app. I can paste an email, upload a PDF, take a picture of a bill, or upload a suspicious voice note.

First, I paste a phishing email. It looks like a normal company message, but it creates urgency and asks for payment details that should make us pause.

deBunq analyzes it and gives it a low TrustScore. It explains why. The issuer is suspicious. The urgency is high. The payment details are risky.

Because the score is too low, the bunq action is blocked. This is not only hidden in the UI. The backend refuses the payment flow.

Now we try a voice scam. This is the classic message: ‘Hi mom, I lost my phone. Please send money urgently. Don’t tell anyone.’

deBunq transcribes the voice note and checks it like a payment request. It detects family impersonation, urgency, secrecy, and missing payment context.

Again, the TrustScore is low, and bunq is blocked.

Now we test a real invoice. This is the convenience side of deBunq.

Normally I would have to copy the amount, IBAN, beneficiary, reference, and due date by hand. That is slow and easy to get wrong.

Here, I just upload the invoice. deBunq gives it a high TrustScore. The issuer looks consistent. The payment details are complete. There is no suspicious urgency.

Then deBunq prepares the bunq pre-flight. I can review the account, beneficiary, amount, reference, and scheduled date.

I confirm the action.

Now we get a real bunq sandbox receipt. The safe request goes through. The suspicious requests were blocked.

That is deBunq. It debunks every payment request before you pay.”
