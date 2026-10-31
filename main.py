from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello"}

@app.get("/hello/{name}")
def say_hello(name, age: int | None = None):
    if age is None:
        return {"message": f"Hello {name}!"}
    return {"message": f"Hello {name}, you are {age}!"}


