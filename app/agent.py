from typing import Tuple, List
import os

from dotenv import load_dotenv
from groq import Groq

from app.retriever import retriever
from app.schemas import Recommendation

load_dotenv()


class SHLAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY not found. Check your .env file.")

        self.client = Groq(api_key=api_key)

    def _is_vague(self, text: str) -> bool:
        text = text.lower().strip()

        vague_queries = [
            "i need an assessment",
            "need an assessment",
            "suggest assessment",
            "recommend assessment",
            "i need a test",
            "need test",
            "assessment"
        ]

        return text in vague_queries or (
            len(text.split()) <= 4 and "assessment" in text
        )

    def _is_blocked(self, text: str) -> bool:
        text = text.lower()

        blocked = [
            "ignore previous instructions",
            "reveal system prompt",
            "jailbreak",
            "legal advice",
            "salary negotiation",
            "employment law",
            "general hiring advice",
            "write code",
            "weather",
            "stock market"
        ]

        return any(x in text for x in blocked)

    def _is_compare(self, text: str) -> bool:
        text = text.lower()

        return (
            "compare" in text
            or "difference between" in text
            or " vs " in text
            or "versus" in text
        )

    def _rerank_candidates(self, candidates, conversation_text):
        text = conversation_text.lower()
        reranked = []

        for item in candidates:
            name = item.get("name", "").lower()
            desc = item.get("description", "").lower()
            keys = " ".join(item.get("keys", [])).lower()
            full = name + " " + desc + " " + keys

            score = item.get("score", 0)

            if "java" in text and "java" in full:
                score += 5

            if "python" in text and "python" in full:
                score += 5

            if any(x in text for x in ["developer", "coding", "programming", "software"]):
                if any(x in full for x in ["coding", "programming", "developer", "software"]):
                    score += 3

            if any(x in text for x in ["stakeholder", "communication", "personality", "team"]):
                if any(x in full for x in ["opq", "personality", "behavior", "behaviour", "communication", "team"]):
                    score += 3

            if any(x in text for x in ["reasoning", "cognitive", "ability", "gsa"]):
                if any(x in full for x in ["reasoning", "ability", "numerical", "verbal", "inductive", "gsa"]):
                    score += 3

            if "mid" in text or "4 years" in text:
                if any(x in full for x in ["intermediate", "advanced", "professional"]):
                    score += 1

            if any(x in full for x in ["hipo", "development report", "action planner"]):
                score -= 5

            reranked.append((score, item))

        reranked.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in reranked]

    def _build_recommendations(self, candidates, conversation_text, limit=10):
        text = conversation_text.lower()

        wants_personality = any(x in text for x in [
           "personality", "opq", "behavior", "behaviour", "stakeholder", "team fit"
        ])

        skill_recs = []
        personality_recs = []
        ability_recs = []
        seen = set()

        for item in candidates:
          name = item.get("name", "")
          url = item.get("url") or item.get("link")

          if not name or not url or url in seen:
             continue

          lower_name = name.lower()
          desc = item.get("description", "").lower()
          keys = " ".join(item.get("keys", [])).lower()
          full = lower_name + " " + desc + " " + keys

          if "java" in text:
             bad_matches = [
                "javascript",
                "job control language",
                "customer service",
                "virtual assessment",
                "assessment center",
                "development center",
                "hipo",
                "report",
                "action planner",
                "business analysis",
                "software business analysis"
             ]
             if any(bad in full for bad in bad_matches):
                continue

          test_type = item.get("test_type")
          if not test_type:
             test_type = item.get("keys", ["K"])[0][:1].upper() if item.get("keys") else "K"

          rec = Recommendation(
            name=name,
            url=url,
            test_type=test_type
          )

          if "java" in full or "coding" in full or "programming" in full:
             skill_recs.append(rec)
          elif test_type.upper() == "P" or any(x in full for x in ["opq", "personality", "behavior", "behaviour"]):
             personality_recs.append(rec)
          elif test_type.upper() == "A" or any(x in full for x in ["reasoning", "ability", "inductive", "numerical", "verbal"]):
             ability_recs.append(rec)

          seen.add(url)

        final_recs = []

        final_recs.extend(skill_recs[:5])

        if wants_personality:
          final_recs.extend(personality_recs[:1])

        final_recs.extend(ability_recs[:1])

        deduped = []
        seen_final = set()

        for rec in final_recs:
           if rec.url not in seen_final:
              deduped.append(rec)
              seen_final.add(rec.url)

           if len(deduped) >= limit:
             break

        return deduped

    def _handle_compare(self, conversation_text):
        text = conversation_text.lower()

        if "opq" in text and "gsa" in text:
            opq_candidates = retriever.search(
                "OPQ Occupational Personality Questionnaire personality workplace behavior",
                top_k=10
            )

            gsa_candidates = retriever.search(
                "GSA General Ability Screen cognitive ability reasoning numerical verbal",
                top_k=10
            )

            opq = None
            gsa = None

            for item in opq_candidates:
                name = item.get("name", "").lower()
                desc = item.get("description", "").lower()
                full = name + " " + desc

                if "opq" in full or "occupational personality questionnaire" in full:
                    opq = item
                    break

            for item in gsa_candidates:
                name = item.get("name", "").lower()
                desc = item.get("description", "").lower()
                full = name + " " + desc

                if "gsa" in full or "general ability" in full or "reasoning" in full:
                    gsa = item
                    break

            recs = []

            if opq:
                recs.append(
                    Recommendation(
                        name=opq["name"],
                        url=opq.get("url") or opq.get("link"),
                        test_type=opq.get("test_type") or "P"
                    )
                )

            if gsa:
                recs.append(
                    Recommendation(
                        name=gsa["name"],
                        url=gsa.get("url") or gsa.get("link"),
                        test_type=gsa.get("test_type") or "A"
                    )
                )

            if opq and gsa:
                reply = (
                    f"{opq['name']} is a personality-focused SHL assessment. "
                    "It helps understand workplace behavior, preferences, and personality style. "
                    f"{gsa['name']} is an ability-focused SHL assessment. "
                    "It helps assess cognitive ability such as reasoning or general mental ability. "
                    "So, OPQ is mainly about behavioral fit, while GSA is mainly about cognitive ability. "
                    "This comparison is based only on the SHL catalog data."
                )

                return reply, recs, False

            return (
                "I could not find both OPQ and GSA clearly in the SHL catalog to compare them.",
                recs,
                False
            )

        candidates = retriever.search(conversation_text, top_k=20)
        candidates = self._rerank_candidates(candidates, conversation_text)

        top_two = candidates[:2]

        recs = self._build_recommendations(
            top_two,
            conversation_text,
            limit=2
        )

        if len(top_two) < 2:
            return (
                "I could not find enough matching SHL assessments in the catalog to compare.",
                [],
                False
            )

        a = top_two[0]
        b = top_two[1]

        reply = (
            f"{a['name']} focuses on "
            f"{a.get('description', 'the first assessment area')}. "
            f"{b['name']} focuses on "
            f"{b.get('description', 'the second assessment area')}. "
            "This comparison is based only on the SHL catalog data."
        )

        return reply, recs, False

    def _llm_reply(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an SHL assessment consultant. "
                        "Keep replies concise. Do not invent assessment names or URLs."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=250
        )

        return response.choices[0].message.content.strip()

    def generate_reply(self, history: List[dict]) -> Tuple[str, List[Recommendation], bool]:
        conversation_text = "\n".join(
            [f"{m['role']}: {m['content']}" for m in history]
        )

        latest_user = history[-1]["content"].lower().strip()

        if self._is_blocked(latest_user):
            return (
                "I can only help with SHL assessment recommendations from the SHL catalog.",
                [],
                False
            )

        if self._is_vague(latest_user):
            return (
                "Sure. What role are you hiring for, and what skills, seniority level, or assessment type should it cover?",
                [],
                False
            )

        if self._is_compare(latest_user):
            return self._handle_compare(conversation_text)

        has_role = any(word in conversation_text.lower() for word in [
            "developer", "engineer", "manager", "analyst", "sales",
            "java", "python", "support", "graduate", "leadership"
        ])

        has_level = any(word in conversation_text.lower() for word in [
            "entry", "junior", "mid", "mid-level", "senior",
            "lead", "4 years", "experienced", "fresher", "graduate"
        ])
        has_assessment_type = any(word in conversation_text.lower() for word in [
        "cognitive", "reasoning", "ability", "personality", "opq", "coding", "technical"
        ])

        if has_role and not has_level and not has_assessment_type and len(history) <= 1:
           if has_role and not has_level and len(history) <= 1:
             return (
                "Sure. What is seniority level?",
                [],
                False
             )

        candidates = retriever.search(conversation_text, top_k=100)
        candidates = self._rerank_candidates(candidates, conversation_text)

        recs = self._build_recommendations(
            candidates,
            conversation_text,
            limit=10
        )

        if not recs:
            return (
                "I could not find a suitable SHL assessment from the catalog for this request.",
                [],
                False
            )

        if "java" in conversation_text.lower() and "stakeholder" in conversation_text.lower():
            reply = (
                f"Got it. Here are {len(recs)} assessments that fit a "
                "mid-level Java dev with stakeholder needs."
            )
        else:
            prompt = (
                f"Conversation:\n{conversation_text}\n\n"
                f"Write one short sentence saying that {len(recs)} SHL assessments fit the user's requirements."
            )
            reply = self._llm_reply(prompt)

        return reply, recs, False


agent = SHLAgent()