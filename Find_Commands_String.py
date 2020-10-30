import re
import numpy as np

# querry = "select pessoa.nome,pessoa.idade from pessoa where pessa.idade = 20"
# querry = "select nome,idade,tipo_c from (select * from cliente join cartao on cartao.usuario = cliente.usuario),batata"
querry = "SELECT LNAME FROM EMPLOYEE, WORKS_ON, PROJECT WHERE PNAME = ‘Aquarius’ OR project.PNUMBER = PNO AND ESSN = SSN AND BDATE > ‘1957-12-31’"
querry = querry.lower()
comandos = ["select ", " from ", " where ", " join ", " on ", "order by"]
operadores_ilogicos = ["=", ">", "<", "<=", ">=", "<>"]
operadores_logicos = [" and ", " or "," in ", " not in ", " like "]


# PNAME = ‘Aquarius’ AND project.PNUMBER = PNO AND ESSN = SSN AND BDATE > ‘1957-12-31’

def split_operators(operadores_ilogicos, operadores_logicos, query: str):
    operadores_logicos_postions = []
    for operador in operadores_logicos:
        query = query.replace(operador, "!_!")
        operadores_logicos_postions.extend([(m.start(), operador) for m in re.finditer(operador, querry)])

    operadores_logicos_postions.sort(key=lambda tup: tup[0])
    query = query.split("!_!")

    conditions = []
    for operador in operadores_ilogicos:
        for i in query:
            if operador in i:
                infos = i.split(operador)
                infos.append(operador)
                conditions.append(tuple(infos))

    print(operadores_logicos_postions)
    print(conditions)

    return operadores_logicos_postions,conditions


select_postions = [m.start() for m in re.finditer("select", querry)]
select_postions.reverse()

sub_querrys = {}

print(querry)

for i, postion in enumerate(select_postions):
    key = f"!{i}!"
    sub_querry = querry[postion:].split(")")[0]
    querry = querry.replace(f"({sub_querry})", key)

    result = {}

    sub_postions = []
    for comando in comandos:
        sub_postion = sub_querry.find(comando)
        if sub_postion == -1:
            continue

        sub_postions.append((comando, sub_postion))

    sub_postions.sort(key=lambda tup: tup[1])

    result["query"] = sub_querry
    for i, current_data in enumerate(sub_postions):
        if i != len(sub_postions) - 1:
            next_data = sub_postions[i + 1]
            result[current_data[0]] = sub_querry[current_data[1]: next_data[1]]
        else:
            result[current_data[0]] = sub_querry[current_data[1]:]

    sub_querrys[key] = result

# for key in sub_querrys:
#     print(key)
#     i = sub_querrys[key]
#     for key2 in sub_querrys[key]:
#         print(f"{key2}: {i[key2]}")


a = sub_querrys["!0!"][" where "].replace("where ", "")
split_operators(operadores_ilogicos, operadores_logicos, a)

# print(sub_querrys)
# print(querry)

# for comando in comandos:
#     print("----------------")
#     print(comando)
#     result = [m.start() for m in re.finditer(comando, sql)]
#
#     if len(result) > 0:
#         positions.update({comando: result})
#     print(result)
