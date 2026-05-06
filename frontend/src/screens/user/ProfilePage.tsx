'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import Icon from '../../components/ui/Icon';
import { useAuth } from '../../stores/authContext';
import { authApi } from '../../api/auth';
import type { UserUpdateRequest } from '../../api/auth';

type Section = 'info' | 'password' | 'danger';

export default function ProfilePage() {
  const { user, setUser, logout } = useAuth();
  const router = useRouter();
  const [section, setSection] = useState<Section>('info');

  // 이름 수정
  const [name, setName] = useState(user?.name ?? '');
  const [nameSuccess, setNameSuccess] = useState('');
  const [nameError, setNameError] = useState('');

  // 비밀번호 변경
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwSuccess, setPwSuccess] = useState('');
  const [pwError, setPwError] = useState('');

  // 계정 탈퇴
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const updateMutation = useMutation({
    mutationFn: (body: UserUpdateRequest) => authApi.updateMe(body),
    onSuccess: (updated) => {
      setUser(updated);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: authApi.deleteMe,
    onSuccess: async () => {
      await logout();
      router.replace('/login');
    },
  });

  function handleNameSubmit(e: React.FormEvent) {
    e.preventDefault();
    setNameError('');
    setNameSuccess('');
    const trimmed = name.trim();
    if (!trimmed) { setNameError('이름을 입력해 주세요.'); return; }
    if (trimmed === (user?.name ?? '')) { setNameError('변경할 내용이 없습니다.'); return; }
    updateMutation.mutate(
      { name: trimmed },
      {
        onSuccess: () => setNameSuccess('이름이 저장되었습니다.'),
        onError: (e: unknown) => {
          const err = e as { response?: { data?: { message?: string } } };
          setNameError(err.response?.data?.message ?? '저장에 실패했습니다.');
        },
      },
    );
  }

  function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPwError('');
    setPwSuccess('');
    if (!currentPw) { setPwError('현재 비밀번호를 입력하세요.'); return; }
    if (newPw.length < 8) { setPwError('새 비밀번호는 8자 이상이어야 합니다.'); return; }
    if (newPw !== confirmPw) { setPwError('새 비밀번호가 일치하지 않습니다.'); return; }
    updateMutation.mutate(
      { current_password: currentPw, new_password: newPw },
      {
        onSuccess: () => {
          setPwSuccess('비밀번호가 변경되었습니다. 다시 로그인해 주세요.');
          setCurrentPw('');
          setNewPw('');
          setConfirmPw('');
        },
        onError: (e: unknown) => {
          const err = e as { response?: { data?: { message?: string } } };
          setPwError(err.response?.data?.message ?? '비밀번호 변경에 실패했습니다.');
        },
      },
    );
  }

  function handleDeleteAccount() {
    if (deleteConfirm !== '탈퇴합니다') return;
    deleteMutation.mutate();
  }

  const tabs: { key: Section; label: string; icon: 'user' | 'lock' | 'shield' }[] = [
    { key: 'info', label: '기본 정보', icon: 'user' },
    { key: 'password', label: '비밀번호 변경', icon: 'lock' },
    { key: 'danger', label: '계정 탈퇴', icon: 'shield' },
  ];

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-[22px] font-bold text-m-text tracking-tight">내 정보</h1>
        <p className="text-[14px] text-m-muted mt-1">계정 정보를 확인하고 수정할 수 있습니다.</p>
      </div>

      {/* Profile header card */}
      <div className="bg-m-surface border border-m-border rounded-xl p-5 mb-5 flex items-center gap-4">
        <div className="w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center text-amber-800 text-[18px] font-bold flex-shrink-0">
          {user?.name?.slice(0, 2) ?? '??'}
        </div>
        <div>
          <p className="text-[16px] font-bold text-m-text">{user?.name ?? '이름 없음'}</p>
          <p className="text-[13px] text-m-muted">{user?.email}</p>
          <span className={`inline-block mt-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${
            user?.role === 'ADMIN'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-green-100 text-green-700'
          }`}>
            {user?.role === 'ADMIN' ? '관리자' : '일반 사용자'}
          </span>
        </div>
        <div className="ml-auto text-right">
          <p className="text-[11px] text-m-subtle">가입일</p>
          <p className="text-[12px] text-m-muted font-medium">
            {user?.created_at ? new Date(user.created_at).toLocaleDateString('ko-KR') : '-'}
          </p>
        </div>
      </div>

      {/* Tab nav */}
      <div className="flex gap-1 mb-5 bg-m-surface-alt rounded-xl p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setSection(tab.key)}
            className={`flex-1 flex items-center justify-center gap-1.5 h-9 rounded-lg text-[13px] font-medium transition-colors ${
              section === tab.key
                ? 'bg-m-surface text-m-text shadow-sm'
                : 'text-m-muted hover:text-m-text'
            }`}
          >
            <Icon name={tab.icon} size={14} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Section: 기본 정보 */}
      {section === 'info' && (
        <div className="bg-m-surface border border-m-border rounded-xl p-5">
          <h2 className="text-[15px] font-semibold text-m-text mb-4">기본 정보 수정</h2>
          <form onSubmit={handleNameSubmit} className="flex flex-col gap-4">
            <div>
              <label className="text-[12px] font-medium text-m-muted block mb-1.5">이메일</label>
              <input
                value={user?.email ?? ''}
                disabled
                className="w-full h-10 px-3 rounded-lg border border-m-border bg-m-surface-alt text-[13px] text-m-subtle"
              />
              <p className="text-[11px] text-m-subtle mt-1">이메일은 변경할 수 없습니다.</p>
            </div>
            <div>
              <label className="text-[12px] font-medium text-m-muted block mb-1.5">이름</label>
              <input
                value={name}
                onChange={(e) => { setName(e.target.value); setNameError(''); setNameSuccess(''); }}
                maxLength={50}
                placeholder="이름을 입력하세요"
                className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
              />
            </div>

            {nameError && (
              <p className="text-[12px] text-red-600 bg-red-50 px-3 py-2 rounded-lg">{nameError}</p>
            )}
            {nameSuccess && (
              <p className="text-[12px] text-green-700 bg-green-50 px-3 py-2 rounded-lg">{nameSuccess}</p>
            )}

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="h-9 px-5 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors disabled:opacity-50"
              >
                {updateMutation.isPending ? '저장 중...' : '저장'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Section: 비밀번호 변경 */}
      {section === 'password' && (
        <div className="bg-m-surface border border-m-border rounded-xl p-5">
          <h2 className="text-[15px] font-semibold text-m-text mb-4">비밀번호 변경</h2>
          <form onSubmit={handlePasswordSubmit} className="flex flex-col gap-4">
            <div>
              <label className="text-[12px] font-medium text-m-muted block mb-1.5">현재 비밀번호</label>
              <input
                type="password"
                value={currentPw}
                onChange={(e) => { setCurrentPw(e.target.value); setPwError(''); }}
                className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
                placeholder="현재 비밀번호"
              />
            </div>
            <div>
              <label className="text-[12px] font-medium text-m-muted block mb-1.5">새 비밀번호</label>
              <input
                type="password"
                value={newPw}
                onChange={(e) => { setNewPw(e.target.value); setPwError(''); }}
                minLength={8}
                className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
                placeholder="8자 이상"
              />
            </div>
            <div>
              <label className="text-[12px] font-medium text-m-muted block mb-1.5">새 비밀번호 확인</label>
              <input
                type="password"
                value={confirmPw}
                onChange={(e) => { setConfirmPw(e.target.value); setPwError(''); }}
                className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
                placeholder="새 비밀번호 재입력"
              />
            </div>

            {pwError && (
              <p className="text-[12px] text-red-600 bg-red-50 px-3 py-2 rounded-lg">{pwError}</p>
            )}
            {pwSuccess && (
              <p className="text-[12px] text-green-700 bg-green-50 px-3 py-2 rounded-lg">{pwSuccess}</p>
            )}

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="h-9 px-5 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors disabled:opacity-50"
              >
                {updateMutation.isPending ? '변경 중...' : '비밀번호 변경'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Section: 계정 탈퇴 */}
      {section === 'danger' && (
        <div className="bg-m-surface border border-red-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Icon name="shield" size={16} color="#dc2626" />
            <h2 className="text-[15px] font-semibold text-red-600">계정 탈퇴</h2>
          </div>
          <p className="text-[13px] text-m-muted mb-4 leading-relaxed">
            탈퇴 시 모든 이력서, 매칭 기록이 삭제되며 복구할 수 없습니다. 신중하게 결정해 주세요.
          </p>
          <div className="bg-red-50 rounded-lg p-4 mb-4">
            <ul className="text-[12px] text-red-700 flex flex-col gap-1.5">
              <li>• 업로드한 이력서 파일과 파싱 데이터 삭제</li>
              <li>• AI 매칭 기록 및 분석 결과 삭제</li>
              <li>• 로그인 정보 및 계정 정보 삭제</li>
              <li>• 탈퇴 후 동일 이메일로 재가입 불가</li>
            </ul>
          </div>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="h-9 px-5 rounded-lg bg-red-600 text-white text-[13px] font-semibold hover:bg-red-700 transition-colors flex items-center gap-1.5"
          >
            <Icon name="trash" size={14} />
            계정 탈퇴 진행
          </button>
        </div>
      )}

      {/* 탈퇴 확인 모달 */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-[360px] p-6">
            <div className="flex items-center gap-2 mb-3">
              <Icon name="shield" size={18} color="#dc2626" />
              <h3 className="text-[16px] font-bold text-red-600">정말 탈퇴하시겠습니까?</h3>
            </div>
            <p className="text-[13px] text-m-muted mb-4">
              계속하려면 아래에 <strong className="text-m-text">탈퇴합니다</strong>를 입력하세요.
            </p>
            <input
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              placeholder="탈퇴합니다"
              className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-red-400 mb-4"
            />

            {deleteMutation.isError && (
              <p className="text-[12px] text-red-600 bg-red-50 px-3 py-2 rounded-lg mb-3">탈퇴 처리에 실패했습니다. 다시 시도해 주세요.</p>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowDeleteModal(false); setDeleteConfirm(''); }}
                className="h-9 px-4 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt"
              >
                취소
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirm !== '탈퇴합니다' || deleteMutation.isPending}
                className="h-9 px-4 rounded-lg bg-red-600 text-white text-[13px] font-semibold hover:bg-red-700 disabled:opacity-40 transition-colors"
              >
                {deleteMutation.isPending ? '처리 중...' : '탈퇴 확인'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
