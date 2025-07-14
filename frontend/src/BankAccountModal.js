import React, { useState } from 'react';

export default function BankAccountModal({ open, onClose, onSubmit, loading }) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [routingNumber, setRoutingNumber] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [confirmAccountNumber, setConfirmAccountNumber] = useState('');
  const [accountType, setAccountType] = useState('Checking');
  const [error, setError] = useState('');

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!firstName || !lastName || !routingNumber || !accountNumber || !confirmAccountNumber) {
      setError('All fields are required.');
      return;
    }
    if (accountNumber !== confirmAccountNumber) {
      setError('Account numbers do not match.');
      return;
    }
    await onSubmit({
      first_name: firstName,
      last_name: lastName,
      routing_number: routingNumber,
      account_number: accountNumber,
      confirm_account_number: confirmAccountNumber,
      account_type: accountType
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Add bank account</h2>
        <form onSubmit={handleSubmit}>
          <label>Account holder's first Name
            <input type="text" value={firstName} onChange={e => setFirstName(e.target.value)} />
          </label>
          <label>Account holder's last Name
            <input type="text" value={lastName} onChange={e => setLastName(e.target.value)} />
          </label>
          <label>Bank routing number
            <input type="text" value={routingNumber} onChange={e => setRoutingNumber(e.target.value)} />
          </label>
          <label>Bank account number
            <input type="text" value={accountNumber} onChange={e => setAccountNumber(e.target.value)} />
          </label>
          <label>Confirm bank account number
            <input type="text" value={confirmAccountNumber} onChange={e => setConfirmAccountNumber(e.target.value)} />
          </label>
          <div style={{ margin: '10px 0' }}>
            Account Type
            <label style={{ marginLeft: 10 }}>
              <input type="radio" value="Checking" checked={accountType === 'Checking'} onChange={() => setAccountType('Checking')} /> Checking
            </label>
            <label style={{ marginLeft: 10 }}>
              <input type="radio" value="Saving" checked={accountType === 'Saving'} onChange={() => setAccountType('Saving')} /> Saving
            </label>
          </div>
          <div className="modal-note">
            Note: Make sure all your bank details are entered correctly before moving on. Return or voided payments could result in interruption or termination of your coverage.
          </div>
          {error && <div className="modal-error">{error}</div>}
          <div className="modal-actions">
            <button type="submit" disabled={loading}>{loading ? 'Submitting...' : 'done'}</button>
            <button type="button" onClick={onClose}>cancel</button>
          </div>
        </form>
      </div>
      <style>{`
        .modal-overlay {
          position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
          background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 1000;
        }
        .modal-content {
          background: #fff; padding: 32px 32px 16px 32px; border-radius: 8px; min-width: 350px; box-shadow: 0 2px 24px rgba(0,0,0,0.18);
        }
        .modal-content h2 { margin-top: 0; }
        .modal-content label { display: block; margin-bottom: 10px; }
        .modal-content input[type="text"] { width: 100%; padding: 6px; margin-top: 2px; margin-bottom: 6px; border-radius: 4px; border: 1px solid #ccc; }
        .modal-actions { display: flex; gap: 10px; margin-top: 16px; }
        .modal-actions button { padding: 8px 20px; border-radius: 5px; border: none; cursor: pointer; background: #00b4ff; color: #fff; font-weight: 600; }
        .modal-actions button[type="button"] { background: #aaa; }
        .modal-note { font-size: 0.85em; color: #888; margin: 8px 0 0 0; }
        .modal-error { color: #e00; margin-top: 8px; }
      `}</style>
    </div>
  );
}
