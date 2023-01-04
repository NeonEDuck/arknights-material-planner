'use strict'
const totalMaterialContainer = document.querySelector('#total-material-container')
const userSelection = JSON.parse(localStorage.getItem('userSelection') || '[]')

for (const selection of userSelection) {
    const token = [...selection.split('-')]
    const operatorId = token[0]
    const upgrade = token[1]
    const level = token[3] || token[2]
    const number = (token[3])?token[2]:null

    let ckb = document.querySelector(`input[type="checkbox"][data-operator="${operatorId}"][data-upgrade="${upgrade}"][data-level="${level}"]` + ((number)?`[data-number="${number}"]`:''))

    if (ckb) {
        ckb.checked = true
    }
}
calculateTotal()

function htmlToElement(html) {
    let template = document.createElement('template');
    template.innerHTML = html;
    return template.content.firstElementChild;
}

function generateId(htmlElement) {
    return `${htmlElement.dataset.operator}-${htmlElement.dataset.upgrade}-${(htmlElement.dataset.number)?htmlElement.dataset.number+"-":""}${htmlElement.dataset.level}`
}

function calculateTotal() {
    const totalMaterials = {}

    const addItem = (item) => {
        if (!totalMaterials[item.id]) {
            totalMaterials[item.id] = 0
        }
        totalMaterials[item.id] += Number(item.count)
    }

    for (const selection of userSelection) {
        const token = [...selection.split('-')]
        const operatorId = token[0]
        const upgrade = token[1]
        const level = Number(token[3] || token[2])
        const number = Number((token[3])?token[2]:0)

        const operator = operators[operatorId]

        if      (upgrade === 'phase') {
            for (const item of operator.phases[level].evolveCost) {
                addItem(item)
            }
        }
        else if (upgrade === 'skill') {
            for (const item of operator.skills[number].levelUpCosts[level]) {
                addItem(item)
            }
        }
        else if (upgrade === 'uniequip') {
            for (const item of Object.values(operator.uniequips[number].itemCost)[level]) {
                addItem(item)
            }
        }
    }

    totalMaterialContainer.innerHTML = ''
    for (const mid in totalMaterials) {
        totalMaterialContainer.innerHTML += `
        <div class="item-container">
            <img src="${materials[mid].art}" alt="${materials[mid].name}">
            <span>${totalMaterials[mid]}</span>
        </div>
        `
    }

    console.log(userSelection)

    localStorage.setItem('userSelection', JSON.stringify(userSelection))
}

document.querySelectorAll('.select-ckb').forEach(ckb => {
    ckb.addEventListener('click', () => {
        if (ckb.checked) {
            userSelection.push(generateId(ckb))
        }
        else {
            while (true) {
                const index = userSelection.indexOf(generateId(ckb))
                if (index === -1) {
                    break
                }
                userSelection.splice(index, 1)
            }
        }

        calculateTotal()
    })
});

document.querySelectorAll('.select-all-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll(`.select-ckb[data-operator="${btn.dataset.operator}"][data-upgrade="skill"][data-number="${btn.dataset.number}"]`).forEach((ckb) => {
            if (!ckb.checked) {
                ckb.click();
            }
        })
    })
});

document.querySelectorAll('.unselect-all-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll(`.select-ckb[data-operator="${btn.dataset.operator}"][data-upgrade="skill"][data-number="${btn.dataset.number}"]`).forEach((ckb) => {
            if (ckb.checked) {
                ckb.click();
            }
        })
    })
});

document.querySelector('#select-all-btn').addEventListener('click', () => {
    document.querySelectorAll('.select-ckb').forEach((ckb) => {
        if (!ckb.checked) {
            ckb.checked = true;
            userSelection.push(generateId(ckb))
        }
    })
    calculateTotal()
})

document.querySelector('#clear-all-btn').addEventListener('click', () => {
    document.querySelectorAll('.select-ckb').forEach((ckb) => {
        if (ckb.checked) {
            ckb.checked = false;
            while (true) {
                const index = userSelection.indexOf(generateId(ckb))
                if (index === -1) {
                    break
                }
                userSelection.splice(index, 1)
            }
        }
    })
    calculateTotal()
})

const serachBox = document.querySelector('#search-box')
const serachBoxSuggestion = document.querySelector('#search-box-suggestion')
serachBox.addEventListener('keyup', () => {
    serachBoxSuggestion.innerHTML = ''
    const text = serachBox.value.trim()
    if (text.length === 0) {
        return
    }

    let i = 0
    const regex = RegExp(`.*${text}.*`, 'i')
    for (const operator of Object.values(operators).filter(x => (x.name.match(regex)))) {
        if (i++ >= 10) {
            break
        }
        const li = htmlToElement(`
            <li>${operator.name}</li>
        `)
        li.addEventListener('click', () => {
            serachBox.value = operator.name
            serachBoxSuggestion.innerHTML = ''
        })
        serachBoxSuggestion.appendChild(li)
    }
})

const plannerFooter = document.querySelector('#planner-footer')
const plannerFooterExpandBtn = document.querySelector('#planner-footer__expand-btn')

plannerFooterExpandBtn.addEventListener('click', () => {
    plannerFooter.classList.toggle('expanded')
})