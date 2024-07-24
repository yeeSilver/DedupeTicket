// api.js

// NLB URL을 변수로 지정합니다.
const NLB_URL = 'http://nlb-was-75ce2cfbf3099c30.elb.ap-northeast-2.amazonaws.com';

// Payment 요청을 보내는 함수
async function sendPaymentRequest(paymentDetails) {
    try {
        const response = await fetch(`${NLB_URL}/process-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(paymentDetails)
        });

        const result = await response.json();
        if (response.ok) {
            return { success: true, data: result };
        } else {
            return { success: false, message: result.message };
        }
    } catch (error) {
        console.error('Error:', error);
        return { success: false, message: 'Error sending payment request.' };
    }
}

// 다른 API 호출 함수도 필요에 따라 추가할 수 있습니다.

export { sendPaymentRequest };
