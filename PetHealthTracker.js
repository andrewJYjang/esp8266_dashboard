import React, { useState } from 'react';
import { Calendar, Plus, Trash2, FileText, Syringe, Pill, Heart } from 'lucide-react';

export default function PetHealthTracker() {
  const [pets, setPets] = useState([
    { id: 1, name: '뽀삐', type: '강아지', breed: '푸들' }
  ]);
  
  const [records, setRecords] = useState([
    {
      id: 1,
      petId: 1,
      date: '2025-10-15',
      type: 'vaccination',
      title: 'DHPPL 접종',
      description: '5차 종합백신 접종 완료',
      nextDate: '2026-10-15'
    }
  ]);

  const [showForm, setShowForm] = useState(false);
  const [selectedPet, setSelectedPet] = useState(1);
  const [formData, setFormData] = useState({
    date: '',
    type: 'checkup',
    title: '',
    description: '',
    nextDate: ''
  });

  const recordTypes = {
    vaccination: { label: '예방접종', icon: Syringe, color: 'bg-blue-100 text-blue-600' },
    checkup: { label: '건강검진', icon: Heart, color: 'bg-green-100 text-green-600' },
    medication: { label: '투약', icon: Pill, color: 'bg-purple-100 text-purple-600' },
    disease: { label: '질병', icon: FileText, color: 'bg-red-100 text-red-600' }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const newRecord = {
      id: Date.now(),
      petId: selectedPet,
      ...formData
    };
    setRecords([newRecord, ...records]);
    setFormData({ date: '', type: 'checkup', title: '', description: '', nextDate: '' });
    setShowForm(false);
  };

  const deleteRecord = (id) => {
    setRecords(records.filter(r => r.id !== id));
  };

  const filteredRecords = records.filter(r => r.petId === selectedPet);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">🐾 반려동물 건강 기록부</h1>
          
          {/* Pet Selection */}
          <div className="flex gap-3 mb-4">
            {pets.map(pet => (
              <button
                key={pet.id}
                onClick={() => setSelectedPet(pet.id)}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  selectedPet === pet.id
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {pet.name} ({pet.type})
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowForm(!showForm)}
            className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center justify-center gap-2"
          >
            <Plus size={20} />
            새 기록 추가
          </button>
        </div>

        {/* Add Record Form */}
        {showForm && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">기록 추가</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">날짜</label>
                <input
                  type="date"
                  required
                  value={formData.date}
                  onChange={(e) => setFormData({...formData, date: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">유형</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  {Object.entries(recordTypes).map(([key, {label}]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">제목</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  placeholder="예: DHPPL 접종, 피부병 치료"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">상세 내용</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="증상, 처방, 특이사항 등"
                  rows="3"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">다음 예정일 (선택)</label>
                <input
                  type="date"
                  value={formData.nextDate}
                  onChange={(e) => setFormData({...formData, nextDate: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700 transition"
                >
                  저장
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-lg font-medium hover:bg-gray-300 transition"
                >
                  취소
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Records List */}
        <div className="space-y-4">
          {filteredRecords.length === 0 ? (
            <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
              <p className="text-gray-500 text-lg">아직 기록이 없습니다</p>
              <p className="text-gray-400 mt-2">새 기록을 추가해보세요</p>
            </div>
          ) : (
            filteredRecords.map(record => {
              const RecordIcon = recordTypes[record.type].icon;
              return (
                <div key={record.id} className="bg-white rounded-xl shadow-md p-5 hover:shadow-lg transition">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className={`p-3 rounded-lg ${recordTypes[record.type].color}`}>
                        <RecordIcon size={24} />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${recordTypes[record.type].color}`}>
                            {recordTypes[record.type].label}
                          </span>
                          <span className="text-sm text-gray-500 flex items-center gap-1">
                            <Calendar size={14} />
                            {record.date}
                          </span>
                        </div>
                        
                        <h3 className="text-lg font-semibold text-gray-800 mb-1">
                          {record.title}
                        </h3>
                        
                        {record.description && (
                          <p className="text-gray-600 text-sm mb-2">{record.description}</p>
                        )}
                        
                        {record.nextDate && (
                          <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 mt-3">
                            <p className="text-sm text-amber-800">
                              📅 다음 예정: {record.nextDate}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => deleteRecord(record.id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50 p-2 rounded-lg transition"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
