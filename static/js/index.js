'use strict'
const totalMaterialContainer = document.querySelector('#total-material-container')
const userSelection = []

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
        const level = token[3] || token[2]
        const number = (token[3])?token[2]:0

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
}

document.querySelectorAll('.select-ckb').forEach(ckb => {
    ckb.addEventListener('click', () => {
        if (ckb.checked) {
            userSelection.push(generateId(ckb))
        }
        else {
            const index = userSelection.indexOf(generateId(ckb))
            if (index !== -1) {
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

document.querySelector('#all-btn').addEventListener('click', () => {
    document.querySelectorAll('.select-ckb').forEach((ckb) => {
        if (!ckb.checked) {
            ckb.checked = true;
            userSelection.push(generateId(ckb))
        }
    })
    calculateTotal()
})