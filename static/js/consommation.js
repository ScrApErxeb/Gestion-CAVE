let produits = [];
let abonnes = [];

document.addEventListener('DOMContentLoaded', () => {
    chargerAbonnes();
    chargerProduits();
    chargerConsommations();

    document.getElementById('venteForm').addEventListener('submit', enregistrerVente);
    document.getElementById('quantite').addEventListener('input', calculerTotal);
    document.getElementById('prix').addEventListener('input', calculerTotal);
    document.getElementById('produit').addEventListener('change', updatePrix);
    document.getElementById('searchAbonne').addEventListener('input', chargerConsommations);
});

async function chargerAbonnes() {
    try {
        const res = await fetch('/api/abonnes');
        const data = await res.json();
        if (!data.success) return;
        abonnes = data.data;
        const select = document.getElementById('abonne');
        select.innerHTML = '<option value="">Sélectionner un abonné</option>';
        abonnes.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.id;
            opt.textContent = `${a.numero_abonne} - ${a.nom_complet}`;
            select.appendChild(opt);
        });
    } catch (e) { console.error(e); }
}

async function chargerProduits() {
    try {
        const res = await fetch('/api/produits');
        const data = await res.json();
        if (!data.success) return;
        produits = data.data;
        const select = document.getElementById('produit');
        select.innerHTML = '<option value="">Sélectionner un produit</option>';
        produits.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.dataset.prix = p.prix_vente;
            opt.dataset.stock = p.stock;
            opt.textContent = `${p.nom} (Stock: ${p.stock} - ${p.prix_vente} FCFA)`;
            select.appendChild(opt);
        });
    } catch (e) { console.error(e); }
}

function updatePrix() {
    const select = document.getElementById('produit');
    const selected = select.options[select.selectedIndex];
    document.getElementById('prix').value = selected?.dataset.prix || 0;
    calculerTotal();
}

function calculerTotal() {
    const quantite = parseFloat(document.getElementById('quantite').value) || 0;
    const prix = parseFloat(document.getElementById('prix').value) || 0;
    document.getElementById('total').value = (quantite * prix).toFixed(0);
}

function resetForm() {
    document.getElementById('venteForm').reset();
    document.getElementById('total').value = '';
}

async function enregistrerVente(event) {
    event.preventDefault();
    const data = {
        abonne_id: parseInt(document.getElementById('abonne').value),
        produit_id: parseInt(document.getElementById('produit').value),
        quantite: parseInt(document.getElementById('quantite').value),
        prix_unitaire: parseFloat(document.getElementById('prix').value),
        note: document.getElementById('note').value
    };
    try {
        const res = await fetch('/api/consommations', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.success) {
            alert('✅ Vente enregistrée avec succès!');
            resetForm();
            chargerConsommations();
            chargerProduits();
        } else alert('❌ Erreur: ' + result.error);
    } catch (e) {
        console.error(e);
        alert('Erreur lors de l\'enregistrement');
    }
}

async function chargerConsommations() {
    try {
        const searchValue = document.getElementById('searchAbonne').value.toLowerCase();
        const res = await fetch('/api/consommations?facturees=false');
        const data = await res.json();
        if (!data.success) return;

        const tbody = document.getElementById('consommationsTable');
        tbody.innerHTML = '';

        let filtered = data.data;
        if (searchValue) {
            filtered = data.data.filter(c => c.abonne.toLowerCase().includes(searchValue));
        }

        filtered.forEach(c => {
            const tr = document.createElement('tr');
            const date = new Date(c.date);
            tr.innerHTML = `
                <td>${date.toLocaleString('fr-FR')}</td>
                <td>${c.abonne}</td>
                <td>${c.produit}</td>
                <td>${c.quantite}</td>
                <td>${c.prix_unitaire.toLocaleString()} FCFA</td>
                <td><strong>${c.montant_total.toLocaleString()} FCFA</strong></td>
                <td>${c.facture_id ? '✅ Facturée' : '⏳ En attente'}</td>
                <td>
                    ${!c.facture_id ? `<button class="btn btn-sm btn-danger" onclick="supprimerConsommation(${c.id})">🗑️</button>` : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error(e); }
}

async function supprimerConsommation(id) {
    if (!confirm('Voulez-vous vraiment supprimer cette consommation ?')) return;
    try {
        const res = await fetch(`/api/consommations/${id}`, { method: 'DELETE' });
        const result = await res.json();
        if (result.success) {
            alert('Consommation supprimée');
            chargerConsommations();
            chargerProduits();
        } else alert('Erreur: ' + result.error);
    } catch (e) { console.error(e); }
}
