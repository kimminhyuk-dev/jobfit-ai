// 다음(카카오) 우편번호 서비스 연동 유틸.
// 별도 API 키가 필요 없는 현업 표준 주소검색 방식.
// https://postcode.map.daum.net/guide

const POSTCODE_SCRIPT_SRC =
  'https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js';

export interface PostcodeResult {
  zonecode: string; // 우편번호 (5자리)
  address: string; // 기본주소 (도로명 또는 지번)
}

interface DaumPostcodeData {
  zonecode: string;
  roadAddress: string;
  jibunAddress: string;
  userSelectedType: 'R' | 'J';
  buildingName?: string;
  apartment?: 'Y' | 'N';
}

interface DaumPostcode {
  open: () => void;
}

interface DaumNamespace {
  Postcode: new (options: {
    oncomplete: (data: DaumPostcodeData) => void;
    onclose?: () => void;
  }) => DaumPostcode;
}

declare global {
  interface Window {
    daum?: { Postcode: DaumNamespace['Postcode'] };
  }
}

let loadPromise: Promise<void> | null = null;

function loadScript(): Promise<void> {
  if (typeof window === 'undefined') return Promise.reject(new Error('no window'));
  if (window.daum?.Postcode) return Promise.resolve();
  if (loadPromise) return loadPromise;

  loadPromise = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script');
    script.src = POSTCODE_SCRIPT_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      loadPromise = null;
      reject(new Error('주소검색 서비스를 불러오지 못했습니다.'));
    };
    document.head.appendChild(script);
  });
  return loadPromise;
}

/** 주소검색 팝업을 열고 선택 결과(우편번호 + 기본주소)를 콜백으로 전달한다. */
export async function openPostcodeSearch(
  onComplete: (result: PostcodeResult) => void,
): Promise<void> {
  await loadScript();
  if (!window.daum?.Postcode) {
    throw new Error('주소검색 서비스를 사용할 수 없습니다.');
  }
  new window.daum.Postcode({
    oncomplete: (data) => {
      const address =
        data.userSelectedType === 'R' ? data.roadAddress : data.jibunAddress;
      const withBuilding =
        data.buildingName && data.apartment === 'Y'
          ? `${address} (${data.buildingName})`
          : address;
      onComplete({ zonecode: data.zonecode, address: withBuilding });
    },
  }).open();
}
