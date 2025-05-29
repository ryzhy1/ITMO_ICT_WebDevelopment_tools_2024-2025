from fastapi import FastAPI, HTTPException
from typing_extensions import TypedDict
from models import *

app = FastAPI()

temp_bd = [
    {
        "id": 1,
        "race": "director",
        "name": "Мартынов Дмитрий",
        "level": 12,
        "profession": {
            "id": 1,
            "title": "Влиятельный человек",
            "description": "Эксперт по всем вопросам"
        },
        "skills":
            [{
                "id": 1,
                "name": "Купле-продажа компрессоров",
                "description": ""

            },
                {
                    "id": 2,
                    "name": "Оценка имущества",
                    "description": ""

                }]
    },
    {
        "id": 2,
        "race": "worker",
        "name": "Андрей Косякин",
        "level": 12,
        "profession": {
            "id": 2,
            "title": "Дельфист-гребец",
            "description": "Уважаемый сотрудник"
        },
        "skills": []
    },
]


@app.get("/")
def hello():
    return "Hello, [username]!"


@app.get("/warriors_list")
def warriors_list() -> List[Warrior]:
    return temp_bd


@app.get("/warrior/{warrior_id}")
def warriors_get(warrior_id: int) -> List[Warrior]:
    return [warrior for warrior in temp_bd if warrior.get("id") == warrior_id]


@app.post("/warrior")
def warriors_create(warrior: Warrior) -> TypedDict('Response', {"status": int, "data": Warrior}):
    warrior_to_append = warrior.model_dump()
    temp_bd.append(warrior_to_append)
    return {"status": 200, "data": warrior}


@app.delete("/warrior/delete{warrior_id}")
def warrior_delete(warrior_id: int):
    for i, warrior in enumerate(temp_bd):
        if warrior.get("id") == warrior_id:
            temp_bd.pop(i)
            break
    return {"status": 201, "message": "deleted"}


@app.put("/warrior{warrior_id}")
def warrior_update(warrior_id: int, warrior: Warrior) -> List[Warrior]:
    for war in temp_bd:
        if war.get("id") == warrior_id:
            warrior_to_append = warrior.model_dump()
            temp_bd.remove(war)
            temp_bd.append(warrior_to_append)
    return temp_bd


@app.get("/professions", response_model=List[Profession])
def list_professions() -> List[Profession]:
    professions = {}
    for warrior in temp_bd:
        profession_data = warrior["profession"]
        profession_id = profession_data["id"]
        if profession_id not in professions:
            professions[profession_id] = Profession(**profession_data)
    return list(professions.values())


@app.get("/profession/{profession_id}", response_model=Profession)
def get_profession(profession_id: int) -> Profession:
    for warrior in temp_bd:
        profession_data = warrior["profession"]
        if profession_data["id"] == profession_id:
            return Profession(**profession_data)


@app.post("/profession", response_model=dict)
def create_profession(profession: Profession) -> dict:
    for warrior in temp_bd:
        if warrior["profession"]["id"] == profession.id:
            raise HTTPException(status_code=400, detail="Profession with this ID already exists")

    if temp_bd:
        temp_bd[0]["profession"] = profession.model_dump()
        return {"status": 200, "data": profession}


@app.put("/profession/{profession_id}", response_model=dict)
def update_profession(profession_id: int, updated_profession: Profession) -> dict:
    for warrior in temp_bd:
        profession_data = warrior["profession"]
        if profession_data["id"] == profession_id:
            warrior["profession"] = updated_profession.model_dump()
            return {"status": 200, "data": updated_profession}


@app.delete("/profession/{profession_id}", response_model=dict)
def delete_profession(profession_id: int) -> dict:
    for warrior in temp_bd:
        profession_data = warrior["profession"]
        if profession_data["id"] == profession_id:
            warrior["profession"] = None
            return {"status": 200, "message": "Profession deleted"}
    raise HTTPException(status_code=404, detail="Profession not found")
