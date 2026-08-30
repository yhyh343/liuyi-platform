# -*- coding: utf-8 -*-
import json
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from models.schema import KnowledgeCase
from config import settings


TERMS = [
    ('六亲', '父母、兄弟、子孙、妻财、官鬼，以卦宫五行为主，与爻支五行生克定六亲', 'term', 0.9),
    ('世爻', '代表求测者自身，世爻旺衰反映自身状态与运势强弱', 'term', 0.95),
    ('应爻', '代表所问之事或他人，应爻旺衰反映事情外部条件', 'term', 0.9),
    ('动爻', '发动之爻，主变化，动则生变，动爻力量大于静爻', 'term', 0.95),
    ('用神', '根据占事类别选取的核心爻位，为解卦的关键依据', 'term', 0.95),
    ('原神', '生用神之爻，为用神之来源与支持力量', 'term', 0.85),
    ('忌神', '克用神之爻，为用神之阻碍与压制力量', 'term', 0.85),
    ('旬空', '甲子旬戌亥空等，空亡之爻暂时无力，出空方应', 'term', 0.9),
    ('月建', '当月地支，主宰一月之旺衰，月建可生克冲合各爻', 'term', 0.95),
    ('日辰', '当日地支，主宰当日之旺衰，日辰可生克冲合各爻', 'term', 0.95),
    ('旺相休囚死', '五行随月令旺相休囚死的五种状态，决定爻力强弱', 'term', 0.9),
    ('六冲六合', '子午冲等六冲主散，寅亥合等六合主聚，影响事态走向', 'term', 0.85),
    ('进神退神', '爻动化进神主前进，化退神主退守', 'term', 0.85),
    ('回头生', '动爻化出之爻生本爻，主事态向有利方向发展', 'term', 0.85),
    ('回头克', '动爻化出之爻克本爻，主事态向不利方向发展', 'term', 0.85),
]

RULES = [
    ('用神选取规则-财运', '测财运以妻财爻为用神，妻财旺相则财路顺畅', 'rule', 0.9),
    ('用神选取规则-工作', '测工作以官鬼爻为用神，官鬼旺相有气则事业有进展', 'rule', 0.9),
    ('用神选取规则-感情', '男测感情以妻财爻为用神，女测感情以官鬼爻为用神', 'rule', 0.9),
    ('用神选取规则-考试', '测考试以父母爻为用神，父母旺相则文思敏捷', 'rule', 0.9),
    ('世应关系判断', '世爻代表自己，应爻代表对方，世应相生相合主顺', 'rule', 0.9),
    ('动爻力量判断', '动爻力量大于静爻，动而化进神则力倍增', 'rule', 0.85),
    ('旺衰综合判断', '爻得月生日生则旺，得月克日克则衰', 'rule', 0.95),
]

CLASSICS = [
    ('增删卜易-用神章', '用神为卦中之提纲，须审用神之旺衰，观世应之生克。用神旺相，诸事皆吉。', 'classic', 0.95),
    ('增删卜易-世应章', '世为己，应为彼。世应相生相合，彼此相得；世应相冲相克，彼此不和。', 'classic', 0.9),
    ('卜筮正宗', '卦有吉凶，不由人谋，然吉凶之中有进退之机。动爻者，事之机也。', 'classic', 0.9),
    ('黄金策-动静章', '静者宜静，动者宜动。静爻逢日冲为暗动，动爻逢日冲为日破。', 'classic', 0.85),
]

SCENES = [
    ('工作事业', '测工作以官鬼爻为用神，世爻旺相则自身状态佳', 'scene', 0.85),
    ('财运投资', '测财运以妻财爻为用神，妻财旺相且有原神生扶则财运佳', 'scene', 0.85),
    ('感情婚姻', '男测感情以妻财为用，女测感情以官鬼为用', 'scene', 0.85),
    ('考试学业', '测考试以父母爻为用神，父母旺相则文章流畅', 'scene', 0.8),
]


def seed_all(db: Session):
    from rag.rag_service import RAGService
    service = RAGService(db)
    all_items = TERMS + RULES + CLASSICS + SCENES
    count = 0
    for title, content, source, quality in all_items:
        existing = db.query(KnowledgeCase).filter(
            KnowledgeCase.title == title, KnowledgeCase.source == source
        ).first()
        if not existing:
            service.add_knowledge(title, content, source, source, quality)
            count += 1
    print('Seeded', count, 'knowledge entries')
    return count


if __name__ == '__main__':
    from db import SessionLocal
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
