// paiement.js
window.facturesImpayees = []; // variable globale accessible partout

document.addEventListener('DOMContentLoaded', () => {
    chargerFactures();
});

// --- Charger toutes les factures depuis l'API ---
async function chargerFactures() {
    try {
        const response = await fetch('/api/factures');
        const data = await response.json();
        if (data.success) {
            window.facturesImpayees = data.data;
            afficherFactures();
            remplirSelectFactures();
        }
    } catch (e) {
        console.error(e);
    }
}




function afficherFactures() {
    const tbody = document.getElementById('paiementsTable');
    tbody.innerHTML = '';

    window.facturesImpayees.forEach(f => {
        const tr = document.createElement('tr');

        const statutBadge = f.reste_a_payer === 0 
            ? '✅ Payée' 
            : (f.reste_a_payer < f.montant_ttc ? '⏳ Partielle' : '❌ Impayée');

        tr.innerHTML = `
            <td>${new Date(f.date_emission).toLocaleDateString('fr-FR')}</td>
            <td>${f.numero_facture}</td>
            <td>${f.abonne}</td>
            <td>${f.montant_ttc.toLocaleString()} FCFA</td>
            <td>${statutBadge}</td>
            <td></td>
        `;
        tbody.appendChild(tr);

        // Actions dynamiques
        const tdActions = tr.querySelector('td:last-child');

        // Bouton voir détails
        const btnVoir = document.createElement('button');
        btnVoir.className = 'btn btn-info';
        btnVoir.textContent = '👁️';
        btnVoir.addEventListener('click', () => voirDetailsFacture(f.id));
        tdActions.appendChild(btnVoir);

        // Bouton ajouter paiement si reste > 0
        if (f.reste_a_payer > 0) {
            const btnPaiement = document.createElement('button');
            btnPaiement.className = 'btn btn-primary';
            btnPaiement.textContent = '💰';
            btnPaiement.addEventListener('click', () => preparerPaiement(f.id));
            tdActions.appendChild(btnPaiement);
        }
    });
}

// --- Remplir select du modal paiement ---
function remplirSelectFactures() {
    const select = document.getElementById('factureSelect');
    if(!select) return;
    select.innerHTML = '<option value="">Sélectionner une facture</option>';
    window.facturesImpayees.forEach(f => {
        const option = document.createElement('option');
        option.value = f.id;
        option.dataset.abonne = f.abonne;
        option.dataset.montant = f.montant_ttc;
        option.dataset.paye = f.montant_paye;
        option.dataset.reste = f.reste_a_payer;
        option.textContent = `${f.numero_facture} - ${f.abonne} (Reste: ${f.reste_a_payer.toLocaleString()} FCFA)`;
        select.appendChild(option);
    });
}

// --- Préparer modal paiement ---
function preparerPaiement(factureId) {
    const select = document.getElementById('factureSelect');
    select.value = factureId;
    afficherDetailsFacture();
    showModal('addPaiementModal');
}

// --- Afficher détails facture dans modal ---
function voirDetailsFacture(factureId) {
    const facture = window.facturesImpayees.find(f => f.id === factureId);
    if (!facture) return;

    document.getElementById('modalFactureAbonne').textContent = facture.abonne;
    document.getElementById('modalFactureMontant').textContent = facture.montant_ttc.toLocaleString();
    document.getElementById('modalFacturePaye').textContent = facture.montant_paye.toLocaleString();
    document.getElementById('modalFactureReste').textContent = facture.reste_a_payer.toLocaleString();
    document.getElementById('modalFactureDate').textContent = new Date(facture.date_emission).toLocaleString();
    document.getElementById('modalFactureMode').textContent = facture.mode_paiement || '-';
    document.getElementById('modalFactureRef').textContent = facture.reference || '-';
    document.getElementById('modalFactureUser').textContent = facture.recu_par || '-';
    document.getElementById('modalFactureNote').textContent = facture.note || '-';

    showModal('detailsFactureModal');
}

// --- Afficher détails dans modal paiement ---
function afficherDetailsFacture() {
    const select = document.getElementById('factureSelect');
    const option = select.options[select.selectedIndex];
    if(option && option.value) {
        document.getElementById('detailsFacture').style.display = 'block';
        document.getElementById('factureAbonne').textContent = option.dataset.abonne;
        document.getElementById('factureMontant').textContent = parseFloat(option.dataset.montant).toLocaleString();
        document.getElementById('facturePaye').textContent = parseFloat(option.dataset.paye).toLocaleString();
        document.getElementById('factureReste').textContent = parseFloat(option.dataset.reste).toLocaleString();
        const montantInput = document.getElementById('montantPaiement');
        montantInput.max = option.dataset.reste;
        montantInput.value = option.dataset.reste;
    } else {
        document.getElementById('detailsFacture').style.display = 'none';
    }
}

// --- Modal helpers ---
function showModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

// --- Enregistrer un paiement ---
async function enregistrerPaiement(event) {
    event.preventDefault();

    const data = {
        facture_id: parseInt(document.getElementById('factureSelect').value),
        montant: parseFloat(document.getElementById('montantPaiement').value),
        mode_paiement: document.getElementById('modePaiement').value,
        reference: document.getElementById('referencePaiement').value
    };

    try {
        const response = await fetch('/api/paiements', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if(result.success){
            closeModal('addPaiementModal');
            await chargerFactures(); // recharge la table pour mise à jour

            alert(`Paiement enregistré par ${result.user_actif || '-'}`);
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch(e){
        console.error(e);
    }
}

// --- Fermer modals en cliquant en dehors ---
window.onclick = function(event) {
    if(event.target.classList.contains('modal')) event.target.style.display='none';
};
