const mockCategories = [
  { id: 1, name: '프론트엔드', description: '웹 프론트엔드 관련 Q&A', postCount: 42, active: true },
  { id: 2, name: '백엔드', description: '서버/API 개발 관련 Q&A', postCount: 35, active: true },
  { id: 3, name: '취업/이직', description: '채용 프로세스, 이직 경험 공유', postCount: 28, active: true },
  { id: 4, name: '이력서 팁', description: '이력서 작성 및 개선 팁', postCount: 17, active: true },
  { id: 5, name: 'DevOps', description: 'CI/CD, 인프라 관련', postCount: 9, active: false },
];

export default function CategoriesPage() {
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[20px] font-bold" style={{ color: '#0f172a', letterSpacing: '-.02em' }}>카테고리 관리</h1>
          <p className="text-[13px] mt-0.5" style={{ color: '#475569' }}>Q&A 게시글을 분류하는 카테고리를 관리합니다.</p>
        </div>
        <button
          className="h-9 px-4 rounded-lg text-white text-[13px] font-semibold flex items-center gap-1.5"
          style={{ background: '#2563eb' }}
        >
          + 카테고리 추가
        </button>
      </div>

      <div className="bg-white border rounded-xl overflow-hidden" style={{ borderColor: '#e2e8f0' }}>
        <table className="w-full text-[13px]">
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              {['이름', '설명', '게시글 수', '상태', '관리'].map((h) => (
                <th key={h} className="text-left px-4 py-3 font-semibold" style={{ color: '#475569' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y" style={{ borderColor: '#f1f5f9' }}>
            {mockCategories.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-semibold" style={{ color: '#0f172a' }}>{c.name}</td>
                <td className="px-4 py-3" style={{ color: '#475569' }}>{c.description}</td>
                <td className="px-4 py-3 font-mono font-semibold" style={{ color: '#0f172a' }}>{c.postCount}</td>
                <td className="px-4 py-3">
                  <span
                    className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                    style={c.active
                      ? { background: '#f0fdf4', color: '#16a34a' }
                      : { background: '#f1f5f9', color: '#94a3b8' }
                    }
                  >
                    {c.active ? '활성' : '비활성'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button className="text-[12px] font-medium hover:underline" style={{ color: '#2563eb' }}>수정</button>
                    <button className="text-[12px] font-medium hover:underline" style={{ color: '#dc2626' }}>삭제</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-[12px] mt-3" style={{ color: '#94a3b8' }}>
        * 수정/삭제/추가 기능은 백엔드 API 연결 후 활성화됩니다.
      </p>
    </div>
  );
}
