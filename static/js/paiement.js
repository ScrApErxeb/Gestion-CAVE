// paiement.js
let facturesImpayees = [];

document.addEventListener('DOMContentLoaded', () => {
    chargerFactures();
});

async function chargerFactures() {
    try {
        const response = await fetch('/api/factures');
        const data = await response.json();
        if (data.success) {
            facturesImpayees = data.data;
            afficherPaiements();
            remplirSelectFactures();
        }
    } catch(e) { console.error(e); }
}

function afficherPaiements() {
    const tbody = document.getElementById('paiementsTable');
    tbody.innerHTML = '';
    facturesImpayees.forEach(f => {
        const tr = document.createElement('tr');
        let statutBadge = f.reste_a_payer === 0 ? '✅ Payée' : (f.reste_a_payer < f.montant_ttc ? '⏳ Partielle' : '❌ Impayée');
        tr.innerHTML = `
            <td>${new Date(f.date_emission).toLocaleDateString()}</td>
            <td>${f.numero_facture}</td>
            <td>${f.abonne}</td>
            <td>${f.montant_ttc.toLocaleString()} FCFA</td>
            <td>${f.mode_paiement || '-'}</td>
            <td>${f.reference || '-'}</td>
            <td>${f.recu_par || '-'}</td>
            <td>${statutBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}

function remplirSelectFactures() {
    const select = document.getElementById('factureSelect');
    select.innerHTML = '<option value="">Sélectionner une facture</option>';
    facturesImpayees.forEach(f => {
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

function afficherDetailsFacture() {
    const select = document.getElementById('factureSelect');
    const option = select.options[select.selectedIndex];
    if(option && option.value) {
        document.getElementById('detailsFacture').style.display = 'block';
        document.getElementById('factureAbonne').textContent = option.dataset.abonne;
        document.getElementById('factureMontant').textContent = parseFloat(option.dataset.montant).toLocaleString();
        document.getElementById('facturePaye').textContent = parseFloat(option.dataset.paye).toLocaleString();
        document.getElementById('factureReste').textContent = parseFloat(option.dataset.reste).toLocaleString();
        document.getElementById('montantPaiement').max = option.dataset.reste;
        document.getElementById('montantPaiement').value = option.dataset.reste;
    } else {
        document.getElementById('detailsFacture').style.display = 'none';
    }
}

function showModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

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
            chargerFactures();
        } else { alert(result.error); }
    } catch(e){ console.error(e); }
}

window.onclick = function(event) {
    if(event.target.classList.contains('modal')) event.target.style.display='none';
};
