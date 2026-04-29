const mockPosts = [
  { id: 1, title: 'React 18 concurrent 기능 정리', category: '프론트엔드', author: '관리자', date: '2026-04-27', views: 284 },
  { id: 2, title: '이직 준비 3개월 후기', category: '취업/이직', author: '관리자', date: '2026-04-25', views: 512 },
  { id: 3, title: 'FastAPI vs Django 비교', category: '백엔드', author: '관리자', date: '2026-04-22', views: 198 },
  { id: 4, title: '이력서 첫 줄에 무엇을 써야 하나', category: '이력서 팁', author: '관리자', date: '2026-04-20', views: 340 },
  { id: 5, title: 'TypeScript 타입 정의 베스트 프랙티스', category: '프론트엔드', author: '관리자', date: '2026-04-18', views: 167 },
];

export default function PostsPage() {
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[20px] font-bold" style={{ color: '#0f172a', letterSpacing: '-.02em' }}>Q&A 게시글 관리</h1>
          <p className="text-[13px] mt-0.5" style={{ color: '#475569' }}>관리자 전용 Q&A 게시글을 관리합니다.</p>
        </div>
        <button
          className="h-9 px-4 rounded-lg text-white text-[13px] font-semibold flex items-center gap-1.5"
          style={{ background: '#2563eb' }}
        >
          + 게시글 작성
        </button>
      </div>

      {/* Filter row */}
      <div className="flex items-center gap-3 mb-4">
        <select
          className="h-9 px-3 rounded-lg border text-[13px] focus:outline-none"
          style={{ borderColor: '#e2e8f0', background: '#fff', color: '#0f172a', minWidth: 140 }}
        >
          <option value="">전체 카테고리</option>
          <option>프론트엔드</option>
          <option>백엔드</option>
          <option>취업/이직</option>
          <option>이력서 팁</option>
        </select>
        <input
          placeholder="제목 검색"
          className="h-9 px-3 rounded-lg border text-[13px] focus:outline-none"
          style={{ borderColor: '#e2e8f0', background: '#fff', color: '#0f172a', width: 220 }}
        />
      </div>

      <div className="bg-white border rounded-xl overflow-hidden" style={{ borderColor: '#e2e8f0' }}>
        <table className="w-full text-[13px]">
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              {['#', '제목', '카테고리', '작성자', '날짜', '조회', '관리'].map((h) => (
                <th key={h} className="text-left px-4 py-3 font-semibold" style={{ color: '#475569' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y" style={{ borderColor: '#f1f5f9' }}>
            {mockPosts.map((p) => (
              <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-mono text-[12px]" style={{ color: '#94a3b8' }}>{p.id}</td>
                <td className="px-4 py-3 font-medium" style={{ color: '#0f172a', maxWidth: 280 }}>
                  <p className="truncate">{p.title}</p>
                </td>
                <td className="px-4 py-3">
                  <span className="text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: '#eff6ff', color: '#2563eb' }}>
                    {p.category}
                  </span>
                </td>
                <td className="px-4 py-3" style={{ color: '#475569' }}>{p.author}</td>
                <td className="px-4 py-3 font-mono text-[12px]" style={{ color: '#94a3b8' }}>{p.date}</td>
                <td className="px-4 py-3 font-mono font-semibold" style={{ color: '#0f172a' }}>{p.views}</td>
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
        * 수정/삭제/작성 기능은 백엔드 API 연결 후 활성화됩니다.
      </p>
    </div>
  );
}
