document.addEventListener('DOMContentLoaded', () => {
    chargerAbonnes();
});

async function chargerAbonnes(recherche = '') {
    try {
        const response = await fetch(`/api/abonnes?recherche=${recherche}`);
        const data = await response.json();

        if (data.success) afficherAbonnes(data.data);
        else alert('Erreur: ' + data.error);

    } catch (error) {
        console.error(error);
        alert("Erreur de chargement des abonnés");
    }
}

function afficherAbonnes(abonnes) {
    const tbody = document.getElementById('abonnesTableBody');
    tbody.innerHTML = '';

    abonnes.forEach(abonne => {
        // Calculer conso totale
        const consoTotal = abonne.factures
            ? abonne.factures.reduce((total, f) => total + (f.montant_ttc || 0), 0)
            : 0;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${abonne.numero_abonne}</td>
            <td><strong>${abonne.nom_complet}</strong></td>
            <td>${abonne.telephone}</td>
            <td>${(abonne.conso_totale || 0).toLocaleString()} FCFA</td>
            <td>${abonne.solde_du.toLocaleString()} FCFA</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="voirAbonne(${abonne.id})">👁️</button>
                <button class="btn btn-sm btn-warning" onclick="modifierAbonne(${abonne.id})">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="desactiverAbonne(${abonne.id})">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}


function rechercherAbonnes() {
    const recherche = document.getElementById('searchInput').value;
    chargerAbonnes(recherche);
}

async function saveAbonne(event) {
    event.preventDefault();

    const id = document.getElementById('abonneId').value;

    const data = {
        nom: document.getElementById('nom').value,
        prenom: document.getElementById('prenom').value,
        telephone: document.getElementById('telephone').value,
        email: document.getElementById('email').value,
        adresse: document.getElementById('adresse').value,
        limite_credit: parseFloat(document.getElementById('limite_credit').value)
    };

    try {
        const url = id ? `/api/abonnes/${id}` : '/api/abonnes';
        const method = id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);
            closeModal('addAbonneModal');
            chargerAbonnes();
        } else {
            alert('Erreur: ' + result.error);
        }

    } catch (error) {
        console.error(error);
        alert("Erreur lors de l'enregistrement");
    }
}

async function modifierAbonne(id) {
    try {
        const response = await fetch(`/api/abonnes/${id}`);
        const data = await response.json();

        if (!data.success) return alert("Erreur : " + data.error);

        const abonne = data.data;

        document.getElementById('modalTitle').textContent = "Modifier l'abonné";
        document.getElementById('abonneId').value = abonne.id;
        document.getElementById('nom').value = abonne.nom;
        document.getElementById('prenom').value = abonne.prenom || '';
        document.getElementById('telephone').value = abonne.telephone;
        document.getElementById('email').value = abonne.email || '';
        document.getElementById('adresse').value = abonne.adresse || '';
        document.getElementById('limite_credit').value = abonne.limite_credit;

        showModal('addAbonneModal');

    } catch (err) {
        console.error(err);
        alert("Erreur de chargement");
    }
}

async function desactiverAbonne(id) {
    if (!confirm("Voulez-vous désactiver cet abonné ?")) return;

    try {
        const response = await fetch(`/api/abonnes/${id}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);
            chargerAbonnes();
        } else alert("Erreur : " + result.error);

    } catch (error) {
        console.error(error);
        alert("Erreur lors de la désactivation");
    }
}

function voirAbonne(id) {
    alert("Fonction en développement");
}

// --- Modal ---
function showModal(id) {
    document.getElementById(id).style.display = 'block';

    if (id === "addAbonneModal" && !document.getElementById('abonneId').value) {
        document.getElementById('abonneForm').reset();
        document.getElementById('modalTitle').textContent = "Nouvel abonné";
    }
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}
