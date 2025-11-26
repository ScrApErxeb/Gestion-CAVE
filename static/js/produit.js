let filtreStockCritique = false;

document.addEventListener('DOMContentLoaded', () => {
    chargerProduits();
});

async function chargerProduits() {
    try {
        const recherche = document.getElementById('searchInput').value;
        let url = `/api/produits?recherche=${recherche}`;
        if (filtreStockCritique) url += '&stock_critique=true';

        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            afficherProduits(data.data);
            mettreAJourStats(data.data);
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

function afficherProduits(produits) {
    const tbody = document.getElementById('produitsTable');
    tbody.innerHTML = '';
    
    produits.forEach(p => {
        const tr = document.createElement('tr');
        if (p.stock_critique) tr.className = 'row-alert';
        tr.innerHTML = `
            <td>${p.code_produit}</td>
            <td><strong>${p.nom}</strong></td>
            <td>${p.type || '-'}</td>
            <td>${p.prix_achat.toLocaleString()} FCFA</td>
            <td>${p.prix_vente.toLocaleString()} FCFA</td>
            <td>${p.stock} ${p.unite} ${p.stock_critique ? '⚠️' : ''}</td>
            <td>${p.marge_pourcentage.toFixed(1)}%</td>
            <td>
                <button class="btn btn-sm btn-warning" onclick="modifierProduit(${p.id})">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="desactiverProduit(${p.id})">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function mettreAJourStats(produits) {
    document.getElementById('totalProduits').textContent = produits.length;
    const critiques = produits.filter(p => p.stock_critique).length;
    document.getElementById('stockCritique').textContent = critiques;
}

function filtrerStockCritique() {
    filtreStockCritique = !filtreStockCritique;
    chargerProduits();
}

async function saveProduit(event) {
    event.preventDefault();

    const id = document.getElementById('produitId').value;
    const data = {
        nom: document.getElementById('nom').value,
        type: document.getElementById('type').value,
        prix_achat: parseFloat(document.getElementById('prix_achat').value),
        prix_vente: parseFloat(document.getElementById('prix_vente').value),
        stock: parseInt(document.getElementById('stock').value),
        stock_alerte: parseInt(document.getElementById('stock_alerte').value),
        unite: document.getElementById('unite').value
    };

    try {
        const url = id ? `/api/produits/${id}` : '/api/produits';
        const method = id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);
            closeModal('addProduitModal');
            chargerProduits();
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'enregistrement');
    }
}

async function modifierProduit(id) {
    try {
        const response = await fetch(`/api/produits/${id}`);
        const data = await response.json();

        if (data.success) {
            const p = data.data;
            document.getElementById('modalTitle').textContent = 'Modifier le produit';
            document.getElementById('produitId').value = p.id;
            document.getElementById('nom').value = p.nom;
            document.getElementById('type').value = p.type || '';
            document.getElementById('prix_achat').value = p.prix_achat;
            document.getElementById('prix_vente').value = p.prix_vente;
            document.getElementById('stock').value = p.stock;
            document.getElementById('stock_alerte').value = p.stock_alerte;
            document.getElementById('unite').value = p.unite;

            showModal('addProduitModal');
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

async function desactiverProduit(id) {
    if (!confirm('Voulez-vous vraiment désactiver ce produit ?')) return;

    try {
        const response = await fetch(`/api/produits/${id}`, { method: 'DELETE' });
        const result = await response.json();

        if (result.success) {
            alert(result.message);
            chargerProduits();
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
    if (modalId === 'addProduitModal' && !document.getElementById('produitId').value) {
        document.getElementById('produitForm').reset();
        document.getElementById('modalTitle').textContent = 'Nouveau produit';
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}
