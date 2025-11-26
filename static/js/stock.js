let produits = [];

document.addEventListener('DOMContentLoaded', () => {
    chargerProduits();
    chargerAlertes();
    chargerMouvements();
});

async function chargerProduits() {
    try {
        const response = await fetch('/api/produits');
        const data = await response.json();
        
        if (data.success) {
            produits = data.data;
            ['produitEntree', 'produitSortie', 'produitAjust'].forEach(selectId => {
                const select = document.getElementById(selectId);
                select.innerHTML = '<option value="">Sélectionner un produit</option>';
                
                data.data.forEach(p => {
                    const option = document.createElement('option');
                    option.value = p.id;
                    option.dataset.stock = p.stock;
                    option.textContent = `${p.nom} (Stock: ${p.stock})`;
                    select.appendChild(option);
                });
            });
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}


async function chargerAlertes() {
    try {
        const response = await fetch('/api/stock/alertes');
        const data = await response.json();

        if (data.success) {

            const tbody = document.getElementById('alertesTable');
            tbody.innerHTML = '';

            // ⚠️ AJOUT DU FILTRE ICI
            const alertes = data.data.filter(p => p.stock <= p.stock_alerte);

            if (alertes.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">✅ Aucun stock critique</td></tr>';
                return;
            }

            alertes.forEach(p => {
                const tr = document.createElement('tr');
                tr.className = 'row-alert';

                tr.innerHTML = `
                    <td>${p.nom}</td>
                    <td><strong>${p.stock} ${p.unite}</strong></td>
                    <td>${p.stock_alerte} ${p.unite}</td>
                    <td>
                        <button class="btn btn-sm btn-success" onclick="reapprovisionnerRapide(${p.id})">📥 Réappro</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

async function chargerMouvements() {
    try {
        const response = await fetch('/api/stock/mouvements');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.getElementById('mouvementsTable');
            tbody.innerHTML = '';
            
            data.data.slice(0, 20).forEach(m => {
                const tr = document.createElement('tr');
                const date = new Date(m.date);
                const typeClass = m.type_mouvement === 'entree' ? 'success' : 'warning';
                tr.innerHTML = `
                    <td>${date.toLocaleString('fr-FR')}</td>
                    <td>${m.produit}</td>
                    <td><span class="badge badge-${typeClass}">${m.type_mouvement}</span></td>
                    <td>${m.quantite}</td>
                    <td>${m.stock_avant}</td>
                    <td><strong>${m.stock_apres}</strong></td>
                    <td>${m.utilisateur}</td>
                    <td>${m.commentaire}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

async function enregistrerEntree(event) {
    event.preventDefault();
    
    const data = {
        produit_id: parseInt(document.getElementById('produitEntree').value),
        quantite: parseInt(document.getElementById('quantiteEntree').value),
        reference: document.getElementById('referenceEntree').value,
        commentaire: document.getElementById('commentaireEntree').value
    };

    try {
        const response = await fetch('/api/stock/entree', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ ' + result.message);
            closeModal('entreeModal');
            document.getElementById('entreeForm').reset();
            chargerProduits();
            chargerAlertes();
            chargerMouvements();
        } else {
            alert('❌ Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

async function enregistrerSortie(event) {
    event.preventDefault();
    
    const data = {
        produit_id: parseInt(document.getElementById('produitSortie').value),
        quantite: parseInt(document.getElementById('quantiteSortie').value),
        commentaire: document.getElementById('commentaireSortie').value
    };

    try {
        const response = await fetch('/api/stock/sortie', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ ' + result.message);
            closeModal('sortieModal');
            document.getElementById('sortieForm').reset();
            chargerProduits();
            chargerAlertes();
            chargerMouvements();
        } else {
            alert('❌ Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

async function enregistrerAjustement(event) {
    event.preventDefault();
    
    const data = {
        produit_id: parseInt(document.getElementById('produitAjust').value),
        nouveau_stock: parseInt(document.getElementById('nouveauStock').value),
        commentaire: document.getElementById('commentaireAjust').value
    };

    try {
        const response = await fetch('/api/stock/ajustement', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ ' + result.message);
            closeModal('ajustementModal');
            document.getElementById('ajustementForm').reset();
            chargerProduits();
            chargerAlertes();
            chargerMouvements();
        } else {
            alert('❌ Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

function afficherStockActuel() {
    const select = document.getElementById('produitAjust');
    const selectedOption = select.options[select.selectedIndex];
    if (selectedOption && selectedOption.dataset.stock) {
        document.getElementById('stockActuel').value = selectedOption.dataset.stock;
    }
}

function reapprovisionnerRapide(produitId) {
    document.getElementById('produitEntree').value = produitId;
    showModal('entreeModal');
}

function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}